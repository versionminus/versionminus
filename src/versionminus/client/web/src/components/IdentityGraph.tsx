import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const NODE_COUNT = 90;
const EDGE_COUNT = 120;

type FlickerState = { intensity: number; target: number };

function randomPointInSphere(radius: number): [number, number, number] {
  const u = Math.random();
  const v = Math.random();
  const theta = 2 * Math.PI * u;
  const phi = Math.acos(2 * v - 1);
  const r = radius * Math.cbrt(Math.random());
  return [
    r * Math.sin(phi) * Math.cos(theta),
    r * Math.sin(phi) * Math.sin(theta),
    r * Math.cos(phi),
  ];
}

export function IdentityGraph() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    const scene = new THREE.Scene();
    scene.background = null;

    const { clientWidth: width, clientHeight: height } = container;

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
    camera.position.set(0, 0, 80);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 25;
    controls.maxDistance = 200;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.3;

    scene.add(new THREE.AmbientLight(0x5c7cfa, 0.55));
    const keyLight = new THREE.DirectionalLight(0xffffff, 0.85);
    keyLight.position.set(30, 50, 40);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0x3f8cff, 0.4);
    rimLight.position.set(-25, -35, -30);
    scene.add(rimLight);

    const nodes = Array.from({ length: NODE_COUNT }, (_, id) => ({
      id,
      position: randomPointInSphere(32),
    }));

    const edgeSet = new Set<string>();
    while (edgeSet.size < EDGE_COUNT) {
      const source = Math.floor(Math.random() * NODE_COUNT);
      let target = Math.floor(Math.random() * NODE_COUNT);
      if (source === target) continue;
      const key = source < target ? `${source}-${target}` : `${target}-${source}`;
      if (edgeSet.has(key)) continue;
      edgeSet.add(key);
    }
    const edges = Array.from(edgeSet).map((pair) => {
      const [a, b] = pair.split('-').map((n) => Number.parseInt(n, 10));
      return { source: a, target: b };
    });

    const degrees = new Array(NODE_COUNT).fill(0);
    edges.forEach(({ source, target }) => {
      degrees[source] += 1;
      degrees[target] += 1;
    });

    const nodeMeshes: THREE.Mesh[] = [];
    const nodeMaterials: THREE.MeshStandardMaterial[] = [];

    nodes.forEach((node) => {
      const degree = degrees[node.id];
      const radius = THREE.MathUtils.clamp(2.6 - degree * 0.12, 0.6, 2.2);
      const geometry = new THREE.SphereGeometry(radius, 18, 18);
      const material = new THREE.MeshStandardMaterial({
        color: new THREE.Color().setHSL(0.62 + Math.random() * 0.05, 0.65, 0.58),
        emissive: new THREE.Color(0x1a1f48),
        emissiveIntensity: 0.25,
        transparent: true,
        opacity: 0.78,
        roughness: 0.4,
        metalness: 0.1,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(node.position[0], node.position[1], node.position[2]);
      scene.add(mesh);
      nodeMeshes.push(mesh);
      nodeMaterials.push(material);
    });

    const positions = new Float32Array(edges.length * 6);
    edges.forEach(({ source, target }, idx) => {
      const start = nodes[source].position;
      const end = nodes[target].position;
      positions.set(start, idx * 6);
      positions.set(end, idx * 6 + 3);
    });
    const edgeGeometry = new THREE.BufferGeometry();
    edgeGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0x4f6bff,
      transparent: true,
      opacity: 0.2,
    });
    const lines = new THREE.LineSegments(edgeGeometry, lineMaterial);
    scene.add(lines);

    const flicker: FlickerState[] = nodeMaterials.map(() => ({ intensity: 0, target: 0 }));

    const chooseFlickerGroup = () => {
      const groupSize = 6 + Math.floor(Math.random() * 10);
      const indices: number[] = [];
      while (indices.length < groupSize) {
        const idx = Math.floor(Math.random() * nodeMaterials.length);
        if (!indices.includes(idx)) indices.push(idx);
      }
      flicker.forEach((state, idx) => {
        state.target = indices.includes(idx) ? 1 : 0;
      });
    };

    const flickerInterval = window.setInterval(chooseFlickerGroup, 2200);
    chooseFlickerGroup();

    let animationFrameId: number;

    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      controls.update();
      flicker.forEach((state, idx) => {
        state.intensity += (state.target - state.intensity) * 0.07;
        const material = nodeMaterials[idx];
        material.emissiveIntensity = 0.25 + state.intensity * 0.7;
        material.opacity = 0.55 + state.intensity * 0.4;
        nodeMeshes[idx].scale.setScalar(1 - state.intensity * 0.12);
      });
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.clearInterval(flickerInterval);
      controls.dispose();
      edgeGeometry.dispose();
      lineMaterial.dispose();
      nodeMeshes.forEach((mesh) => {
        mesh.geometry.dispose();
        (mesh.material as THREE.Material).dispose();
      });
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return <div ref={containerRef} className="identity-graph" />;
}
