// At the top of buildings.js (loaded as type="module")
import * as THREE from "https://cdnjs.cloudflare.com/ajax/libs/three.js/0.180.0/three.module.min.js";

function buildHouse(elementID) {
// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();

  const container = document.getElementById(elementID);
//   const renderer = new THREE.WebGLRenderer();
//   // Set renderer size to the container's size
//   console.log("Container ", container)
  renderer.setSize(container.clientWidth, container.clientHeight);
//   // Add the canvas to your div instead of the body
  container.appendChild(renderer.domElement);

renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

console.log("sdfsdf")

// House wireframe (main box)
const wireFrameMaterial = new THREE.MeshBasicMaterial({ color: 0x00ff00, wireframe: true });
const houseGeometry = new THREE.BoxGeometry(4, 2, 3);
const house = new THREE.Mesh(houseGeometry, wireFrameMaterial);
scene.add(house);

// Door (thin box)
const doorGeometry = new THREE.BoxGeometry(0.8, 1.2, 0.05);
const doorMaterial = new THREE.MeshBasicMaterial({ color: 0xffd700, wireframe: true });
const door = new THREE.Mesh(doorGeometry, doorMaterial);
door.position.set(-1.1, -0.4, 1.525); // At front wall
house.add(door);

// Window (thin box)
const windowGeometry = new THREE.BoxGeometry(0.7, 0.7, 0.05);
const windowMaterial = new THREE.MeshBasicMaterial({ color: 0x87ceeb, wireframe: true });
const win1 = new THREE.Mesh(windowGeometry, windowMaterial);
win1.position.set(0.9, 0, 1.525); // At front wall
house.add(win1);

// Camera position
camera.position.z = 6;

// Animation helpers
let doorOpen = false, windowOpen = false;
function toggleDoor() {
    door.rotation.y = doorOpen ? 0 : -Math.PI/2; // Swing open
    doorOpen = !doorOpen;
}
function toggleWindow() {
    win1.rotation.y = windowOpen ? 0 : Math.PI/2; // Slide open
    windowOpen = !windowOpen;
}
// Example: Call these functions from UI buttons

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
animate();

  // Set up renderer, scene, and camera
//   const container = document.getElementById(elementID);
//   const renderer = new THREE.WebGLRenderer();
//   // Set renderer size to the container's size
//   console.log("Container ", container)
//   renderer.setSize(container.clientWidth, container.clientHeight);
//   // Add the canvas to your div instead of the body
//   container.appendChild(renderer.domElement);
//   renderer.setSize(window.innerWidth, window.innerHeight);
//   document.body.appendChild(renderer.domElement);

//   const scene = new THREE.Scene();
//   const camera = new THREE.PerspectiveCamera(
//     75,
//     window.innerWidth / window.innerHeight,
//     0.1,
//     1000
//   );
//   camera.position.z = 10;

// //   // Set up interaction manager
// //   const interactionManager = new InteractionManager(
// //     renderer,
// //     camera,
// //     renderer.domElement
// //   );

//   // House walls
//   const wallGeometry = new THREE.BoxGeometry(8, 4, 0.2);
//   const wallMaterial = new THREE.MeshBasicMaterial({ color: 0xf5deb3 });
//   const wall = new THREE.Mesh(wallGeometry, wallMaterial);
//   scene.add(wall);

//   // Door
//   const doorGeometry = new THREE.BoxGeometry(1, 2, 0.1);
//   const doorMaterial = new THREE.MeshBasicMaterial({ color: 0x8b4513 });
//   const door = new THREE.Mesh(doorGeometry, doorMaterial);
//   door.position.set(-2.5, -1, 0.2);
//   scene.add(door);
// //   interactionManager.add(door);

//   // Window
//   const windowGeometry = new THREE.BoxGeometry(1.2, 1, 0.1);
//   const windowMaterial = new THREE.MeshBasicMaterial({
//     color: 0x87ceeb,
//     transparent: true,
//     opacity: 0.6,
//   });
//   const windowMesh = new THREE.Mesh(windowGeometry, windowMaterial);
//   windowMesh.position.set(2.5, 0, 0.2);
//   scene.add(windowMesh);
// //   interactionManager.add(windowMesh);

//   // Door opening state
//   let doorOpen = false;
//   door.userData = { rotY: 0 };
//   door.addEventListener("click", () => {
//     doorOpen = !doorOpen;
//   });

//   // Window opening state
//   let windowOpen = false;
//   windowMesh.userData = { rotY: 0 };
//   windowMesh.addEventListener("click", () => {
//     windowOpen = !windowOpen;
//   });

//   // Animation loop
//   function animate() {
//     requestAnimationFrame(animate);

//     // Animate door
//     let targetRotY = doorOpen ? -Math.PI / 2 : 0;
//     door.rotation.y += (targetRotY - door.rotation.y) * 0.1;

//     // Animate window
//     let targetWindowRotY = windowOpen ? Math.PI / 2 : 0;
//     windowMesh.rotation.y += (targetWindowRotY - windowMesh.rotation.y) * 0.1;

//     // interactionManager.update();
//     renderer.render(scene, camera);
//   }
//   animate();
}

window.buildHouse = buildHouse;