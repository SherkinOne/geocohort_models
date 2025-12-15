// buildings.js
import * as THREE from "three";
import { OrbitControls } from "https://unpkg.com/three@0.180.0/examples/jsm/controls/OrbitControls.js";
import { IFCLoader } from "https://cdn.jsdelivr.net/npm/web-ifc-three@0.0.126/IFCLoader.js";
import { IFCROOF, IFCWALL, IFCSLAB, IFCDOOR, IFCWINDOW, IFCBUILDINGSTOREY, IFCFACE } from "web-ifc";

const ifcLoader = new IFCLoader();
let roofSubset = null;
export default async function buildHouse(elementID) {
  const container = document.getElementById(elementID);
  if (!container) return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(
    75,
    container.clientWidth / container.clientHeight,
    0.1,
    1000
  );
  // camera.position.set(15, 150, 15);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  const webIFC = ifcLoader.ifcManager.setWasmPath(
    "https://cdn.jsdelivr.net/npm/web-ifc@0.0.53/"
  );        

  for (const [name, value] of Object.entries(webIFC)) {
    console.log(`${name} = ${value}`);
  }

  // const ifcUrl = "../static/ifc_files/SampleHouse.ifc"; // or .ifc
  const ifcUrl = "../static/ifc_files/BasicHouse.ifc"; // or .ifc
  // const ifcUrl = "../static/ifc_files/2.ifc"; // or .ifc
  showLoading('Loading IFC model...');
  let model;
  let modelID;
  try {
    model = await ifcLoader.loadAsync(ifcUrl);
    modelID = model.modelID;
  } catch (err) {
    hideLoading();
    console.error('Failed to load IFC model', err);
    const errEl = document.createElement('div');
    errEl.style.color = 'red';
    errEl.style.padding = '8px';
    errEl.textContent = 'Failed to load IFC model: ' + (err && err.message ? err.message : String(err));
    container.appendChild(errEl);
    throw err;
  }
  // keep the loading overlay until scanning/subset creation finishes

  // Loading overlay utilities to keep the UI responsive and show progress for large models
  function showLoading(text) {
    try {
      let el = container.querySelector('.ifc-loading-overlay');
      if (!el) {
        el = document.createElement('div');
        el.className = 'ifc-loading-overlay';
        el.style.position = 'absolute';
        el.style.left = 0;
        el.style.top = 0;
        el.style.right = 0;
        el.style.bottom = 0;
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.background = 'rgba(0,0,0,0.4)';
        el.style.color = '#fff';
        el.style.zIndex = 9998;
        el.style.fontSize = '14px';
        container.appendChild(el);
      }
      el.textContent = text || 'Loading...';
      el.style.display = 'flex';
    } catch (e) {}
  }
  function hideLoading() {
    try {
      const el = container.querySelector('.ifc-loading-overlay');
      if (el) el.style.display = 'none';
    } catch (e) {}
  }

  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const box = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());


// 2) Build "everything except roof" view
// Ensure the full model is present in the scene so that hiding the roof subset reveals everything else.
try {
  scene.add(model);
} catch (e) {
  // ignore if already added
}

  // Subset references for toggling
  let noRoofSubset = null;
  let roofOnlySubset = null;
  let roofsHidden = false;

// Helper to collect IDs from a list of IFC types
async function collectIdsForTypes(modelID, types) {
  const set = new Set();
  for (const t of types) {
    if (typeof t !== 'number') continue;
    try {
      const ids = await ifcLoader.ifcManager.getAllItemsOfType(modelID, t, false);
      if (Array.isArray(ids) && ids.length) ids.forEach((id) => set.add(id));
    } catch (err) {
      // ignore unsupported types
    }
  }
  return Array.from(set);
}

// Helper to detect whether a given element is roof-related
async function isElementRoofRelated(modelID, expressID) {
  try {
    const props = await ifcLoader.ifcManager.getItemProperties(modelID, expressID, true);
    const val = (field) => {
      if (field == null) return undefined;
      if (typeof field === 'object' && 'value' in field) return field.value;
      return field;
    };

    // 1) check PredefinedType (common for IfcSlab used as roof)
    const predefined = val(props.PredefinedType) ?? val(props.Predefinedtype) ?? val(props.Predefined_Type);
    if (predefined && String(predefined).toUpperCase().includes('ROOF')) return true;

    // 2) check ObjectType / Name / LongName
    const objectType = val(props.ObjectType) ?? val(props.Object_Type);
    const name = val(props.Name) ?? val(props.LongName) ?? val(props.Long_Name);
    if ((objectType && String(objectType).toLowerCase().includes('roof')) || (name && String(name).toLowerCase().includes('roof'))) {
      return true;
    }

    // 3) inspect property sets / other fields for 'roof' substring
    for (const [k, v] of Object.entries(props)) {
      if (k === 'expressID' || k === 'GlobalId' || k === 'OwnerHistory') continue;
      try {
        const candidate = val(v);
        if (candidate && String(candidate).toLowerCase().includes('roof')) return true;
      } catch (e) {
        // ignore non-string values
      }
    }
  } catch (err) {
    // reading properties may fail for some entity types
    console.warn('isElementRoofRelated error for', expressID, err);
  }
  return false;
}

// Batch-filter function to avoid blocking the main thread for very large models.
async function filterOutRoofsBatched(modelID, ids, opts = {}) {
  const batchSize = opts.batchSize || 200;
  const results = [];
  for (let i = 0; i < ids.length; i += batchSize) {
    const chunk = ids.slice(i, i + batchSize);
    showLoading(`Scanning ${Math.min(i + batchSize, ids.length)}/${ids.length} elements...`);
    // Run checks in parallel for the chunk, but catch errors per-id
    const checks = await Promise.all(chunk.map((id) => isElementRoofRelated(modelID, id).catch((e) => { console.warn('isElementRoofRelated failed for', id, e); return false; })));
    for (let j = 0; j < chunk.length; j++) {
      const id = chunk[j];
      const isRoof = checks[j];
      if (!isRoof) results.push(id);
      else {
        try { roofSet.add(id); } catch (e) {}
      }
    }
    // yield to the event loop so the browser can repaint/respond
    // small pause avoids freezing the tab when models are huge
    // eslint-disable-next-line no-await-in-loop
    await new Promise((res) => setTimeout(res, 0));
  }
  hideLoading();
  return results;
}

// Curated types we want to show (expand this list if you need more types)
const curatedTypes = [IFCWALL, IFCSLAB, IFCDOOR, IFCWINDOW, IFCBUILDINGSTOREY, IFCFACE].filter((t) => typeof t === 'number');
let collected = [];
try {
  showLoading('Collecting element IDs...');
  collected = await collectIdsForTypes(modelID, curatedTypes);
  hideLoading();
} catch (e) {
  hideLoading();
  console.warn('Failed to collect IDs synchronously, proceeding with empty collection', e);
}

// Explicitly get roof IDs (if available)
let roofIds = [];
if (typeof IFCROOF === 'number') {
  try {
    roofIds = await ifcLoader.ifcManager.getAllItemsOfType(modelID, IFCROOF, false);
  } catch (err) {
    roofIds = [];
  }
}

const roofSet = new Set(Array.isArray(roofIds) ? roofIds : []);
// Further filter collected IDs by inspecting their properties to detect roof-markers.
// Use a batched scan to avoid freezing large pages.
let idsWithoutRoof = collected;
if (collected.length > 0) {
  try {
    // Scan only IFCSLAB candidates for roof markers (most roof-like slabs)
    const slabIds = await collectIdsForTypes(modelID, [IFCSLAB]);
    // intersect collected with slabIds to find slab candidates that need property checks
    const slabSet = new Set(slabIds);
    const toCheck = collected.filter((id) => slabSet.has(id));
    if (toCheck.length > 0) {
      // run batched checks only for slab-like elements
      const nonRoofFromSlabs = await filterOutRoofsBatched(modelID, toCheck, { batchSize: 200 });
      // combine non-slab collected IDs (assumed non-roof) with nonRoofFromSlabs
      const nonSlabIds = collected.filter((id) => !slabSet.has(id));
      idsWithoutRoof = nonSlabIds.concat(nonRoofFromSlabs);
      console.log(`Collected ${collected.length} items; scanned ${toCheck.length} slabs, showing ${idsWithoutRoof.length} items.`);
    } else {
      console.log(`Collected ${collected.length} items; no slabs found to scan; showing all collected items.`);
    }
  } catch (e) {
    console.warn('Batched roof detection failed; falling back to excluding IFCROOF only', e);
    // keep idsWithoutRoof as collected but roofSet still contains roofIds from earlier
    idsWithoutRoof = collected.filter((id) => !roofSet.has(id));
  }
}

// If we collected a useful set, create a subset for everything except roofs and hide the roof subset.
if (idsWithoutRoof.length > 0 && typeof ifcLoader.ifcManager.createSubset === 'function') {
  try {
    // Create subset with non-roof IDs and display it
    noRoofSubset = ifcLoader.ifcManager.createSubset({ modelID, ids: idsWithoutRoof, scene, removePrevious: false, customID: 'no-roof' });
    if (noRoofSubset) {
      // Hide the original full model so only the subset is visible
      try { model.visible = false; } catch (e) {}
      roofsHidden = true;
      console.log(`Created no-roof subset (${idsWithoutRoof.length} items), hidden full model.`);
    }
  } catch (err) {
    console.warn('Failed to create no-roof subset, falling back to hide roof subset', err);
  }
} else {
  // Fallback: create a roof-only subset and hide it, leaving the full model visible
  if (roofIds.length > 0 && typeof ifcLoader.ifcManager.createSubset === 'function') {
    try {
      roofOnlySubset = ifcLoader.ifcManager.createSubset({ modelID, ids: roofIds, scene, removePrevious: true, customID: 'roof-only' });
      if (roofOnlySubset) {
        try { roofOnlySubset.visible = false; } catch (e) {}
        roofsHidden = true;
        console.log(`Hid roof-only subset (${roofIds.length} items); full model remains visible.`);
      }
    } catch (err) {
      console.warn('Could not create/hide roof subset; roof may still be visible', err);
    }
  } else {
    console.warn('No non-roof IDs collected and no roof IDs found; model may only contain roofs or API unavailable.');
  }
}

// Toggle helper to show/hide roofs
function setRoofsHidden(hide) {
  try {
    if (hide) {
      if (noRoofSubset) {
        noRoofSubset.visible = true;
        try { model.visible = false; } catch (e) {}
      } else if (roofOnlySubset) {
        try { roofOnlySubset.visible = false; } catch (e) {}
        try { model.visible = true; } catch (e) {}
      }
    } else {
      // show roofs
      if (noRoofSubset) {
        try { noRoofSubset.visible = false; } catch (e) {}
        try { model.visible = true; } catch (e) {}
      } else if (roofOnlySubset) {
        try { roofOnlySubset.visible = true; } catch (e) {}
        try { model.visible = true; } catch (e) {}
      }
    }
    roofsHidden = hide;
    // update button label if present
    const btn = document.getElementById('toggle-roofs-btn');
    if (btn) btn.textContent = roofsHidden ? 'Show Roofs' : 'Hide Roofs';
  } catch (e) {
    console.warn('Error toggling roofs', e);
  }
}

// Add a small toggle button to container
try {
  const toggleBtn = document.createElement('button');
  toggleBtn.id = 'toggle-roofs-btn';
  toggleBtn.style.position = 'absolute';
  toggleBtn.style.zIndex = 9999;
  toggleBtn.style.right = '12px';
  toggleBtn.style.top = '12px';
  toggleBtn.style.padding = '6px 10px';
  toggleBtn.style.background = '#fff';
  toggleBtn.style.border = '1px solid #666';
  toggleBtn.style.cursor = 'pointer';
  toggleBtn.textContent = roofsHidden ? 'Show Roofs' : 'Hide Roofs';
  toggleBtn.addEventListener('click', () => setRoofsHidden(!roofsHidden));
  // ensure container is positioned so absolute button sits on it
  try { container.style.position = container.style.position || 'relative'; } catch (e) {}
  container.appendChild(toggleBtn);
} catch (e) {
  // ignore UI errors
}

// For debugging, expose counts
try {
  const walls = await ifcLoader.ifcManager.getAllItemsOfType(modelID, IFCWALL, false);
  const slabs = await ifcLoader.ifcManager.getAllItemsOfType(modelID, IFCSLAB, false);
  const doors = await ifcLoader.ifcManager.getAllItemsOfType(modelID, IFCDOOR, false);
  const windows = await ifcLoader.ifcManager.getAllItemsOfType(modelID, IFCWINDOW, false);
  // console.log('debug counts -> walls:', walls?.length || 0, 'slabs:', slabs?.length || 0, 'doors:', doors?.length || 0, 'windows:', windows?.length || 0, 'roofCount:', roofSet.size);


  const doorID = Math.floor(Math.random() * (doors.length + 1));
  const windowID = Math.floor(Math.random() * (windows.length + 1));
   toggleDoor(modelID, windows[windowID], scene)
  // toggleDoor(modelID, doors[doorID],scene)

  } catch (e) {}
  // position camera so the model fits in view
  const maxDim = Math.max(size.x, size.y, size.z);
  const dist = maxDim / 5;
  camera.position.set(dist, dist, dist);
  camera.lookAt(0, 0, 0);
  controls.target.set(0, 0, 0);
  controls.update();

  const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
  directionalLight.position.set(1, 1, 1);
  scene.add(directionalLight);

  // scene.add(model);` 

  // move house to origin for convenience
  // model.position.sub(center);
  try {
    if (typeof roofSubset !== 'undefined' && roofSubset) roofSubset.position.sub(center);
  } catch (err) {
    // roofSubset may not exist or not have position - ignore
  }

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();
  return roofSubset;
}

async function toggleDoor(modelID, expressID, scene) {
  const subset = ifcLoader.ifcManager.createSubset({
    modelID,
    ids: [expressID],
    removePrevious: false,
    scene,
    customID: `door-${expressID}`,
  });

  // simple open/close toggle on Y axis
  const isOpen = subset.userData.isOpen || false;
  const targetAngle = isOpen ? 0 : Math.PI / 1.7; // 90°
  subset.userData.isOpen = !isOpen;
  // (Optional) animate over time instead of setting directly
  // Use a pivot object so rotation happens around the subset's center (or hinge)
  try {
    // Reuse existing pivot if present
    let pivot = subset.userData.pivot;
    if (!pivot) {
      // compute bounding box center of the subset
      const box = new THREE.Box3().setFromObject(subset);
      const center = box.getCenter(new THREE.Vector3());

      // create pivot at center and reparent subset under it
      pivot = new THREE.Object3D();
      pivot.position.copy(center);
      // ensure pivot is added to the same scene
      try { scene.add(pivot); } catch (e) { /* ignore if scene access fails */ }
      // offset subset so its geometry aligns with pivot origin
      subset.position.sub(center);
      pivot.add(subset);
      subset.userData.pivot = pivot;
    }

    // animate the pivot rotation instead of subset.rotation
    // If already animating, stop the loop (toggle behavior)
    const desiredOpenAngle = Math.PI / 18; // 45 degrees
    const duration = 4000; // ms per half-cycle
    const easeInOutQuad = (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t);

    if (subset.userData.animating) {
      // stop animation and reset
      subset.userData.animating = false;
      try { pivot.rotation.y = 0; } catch (e) {}
      return;
    }

    subset.userData.animating = true;
    // setup ping-pong loop variables
    let startAngle = pivot.rotation.y || 0;
    let endAngle = desiredOpenAngle;
    let startTime = null;

    function loopStep(now) {
      if (!subset.userData.animating) return;
      if (startTime === null) startTime = now;
      const elapsed = now - startTime;
      const p = Math.min(1, elapsed / duration);
      const eased = easeInOutQuad(p);
      pivot.rotation.y = startAngle + (endAngle - startAngle) * eased;
      if (p < 1) {
        requestAnimationFrame(loopStep);
        return;
      }
      // swap for the next half-cycle
      startTime = null;
      startAngle = endAngle;
      endAngle = (Math.abs(endAngle - desiredOpenAngle) < 1e-6) ? 0 : desiredOpenAngle;
      // continue loop
      requestAnimationFrame(loopStep);
    }
    requestAnimationFrame(loopStep);
  } catch (e) {
    // fallback to immediate set on subset if pivot approach fails
    try { subset.rotation.y = targetAngle; } catch (err) { console.warn('Door rotation failed', err); }
  }
}
