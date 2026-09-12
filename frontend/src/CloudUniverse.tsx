import { Component, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode, MutableRefObject, RefObject } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Box3, PerspectiveCamera, Sphere, Vector3, WebGLRenderer } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CircleHelp, Minus, Pause, Play, Plus, RotateCcw, X } from 'lucide-react';
import type { Topic, Update } from './models.ts';
import { createCameraTransition, createSceneRegistry, particleBudget } from './scene-model.ts';
import type { SceneTopic, Vec3 } from './scene-model.ts';
import { createGalaxyRegistry, createDetailTransition, galaxyDetail } from './galaxy-model.ts';
import type { SceneGalaxy } from './galaxy-model.ts';
import GalaxyVisual, { galaxyColor } from './GalaxyVisual.tsx';
import type { GalaxyMotion } from './GalaxyVisual.tsx';
import { IconControl } from './IconControl.tsx';
import { useSceneObstacles } from './useSceneObstacles.ts';
import type { LabelSizes } from './useSceneObstacles.ts';
import { createLabelPlacer } from './overlay-layout.ts';
import type { Rect } from './overlay-layout.ts';
type Motion = GalaxyMotion & { transition: ReturnType<typeof createDetailTransition> };

type Command = 'in' | 'out' | 'reset';
type Label = { id: string; x: number; y: number; category?: boolean; text?: string; count?: number; memories?: number; matching?: number; opacity: number; interactive: boolean };
type Props = { topics: Topic[]; visibleTopics: Topic[]; selectedId: string | null; updates: Update[];
  onSelect: (id: string, element: HTMLElement) => void; active: boolean; compact: boolean; onFailure: () => void; helpOpen: boolean; onHelpToggle: () => void; onHelpClose: () => void; helpButtonRef: RefObject<HTMLButtonElement | null> };
const colorFor = (topic: Topic) => galaxyColor(topic.category);
const initialCamera = { position: [0, 24, 130] as Vec3, fov: 45, near: .1, far: 5000 };
// Development-only QA overrides, never active with connected API data.
const fixtureQA = import.meta.env.DEV && import.meta.env.VITE_DATA_MODE !== 'api';
const reducedFixture = fixtureQA && new URLSearchParams(location.search).get('motion') === 'reduce';
const contextLossFixture = fixtureQA && new URLSearchParams(location.search).get('scene') === 'context-loss';

class SceneBoundary extends Component<{ onFailure: () => void; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error) { console.warn('3D scene unavailable:', error); this.props.onFailure(); }
  render() { return this.state.failed ? null : this.props.children; }
}
function useReducedMotion() {
  const [reduced, setReduced] = useState(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => { const media = matchMedia('(prefers-reduced-motion: reduce)'); const change = () => setReduced(media.matches);
    media.addEventListener('change', change); return () => media.removeEventListener('change', change); }, []);
  return reduced || reducedFixture;
}
export default function CloudUniverse(props: Props) {
  const root = useRef<HTMLDivElement>(null);
  const { obstacles, labelSizes } = useSceneObstacles(root);
  const registry = useRef(createSceneRegistry());
  const scene = useMemo(() => registry.current.register(props.topics), [props.topics]);
  const clouds = useMemo(() => {
    const visible = new Set(props.visibleTopics.map(t => t.id));
    return scene.filter(t => visible.has(t.topic.id) && t.radius > 0);
  }, [scene, props.visibleTopics]);
  const galaxyRegistry = useRef(createGalaxyRegistry());
  const galaxies = useMemo(() => galaxyRegistry.current.register(scene, new Set(props.visibleTopics.map(t => t.id))), [scene, props.visibleTopics]);
  const motions = useRef(new Map<string, Motion>());
  for (const g of galaxies) if (!motions.current.has(g.id)) motions.current.set(g.id, { detail: 0, elapsed: 0, breathing: false, transition: createDetailTransition() });
  const approach = useRef<(id: string) => void>(() => {});
  const [paused, setPaused] = useState(false);
  const [labels, setLabels] = useState<Label[]>([]);
  const [hovered, setHovered] = useState<string | null>(null);
  const [focused, setFocused] = useState<string | null>(null);
  const command = useRef<(command: Command) => void>(() => {});
  const buttons = useRef(new Map<string, HTMLButtonElement>());
  const reduced = useReducedMotion();
  const publish = useCallback((next: Label[]) => setLabels(old => JSON.stringify(old) === JSON.stringify(next) ? old : next), []);
  useEffect(() => {
    if (!focused?.startsWith('galaxy:')) return;
    const galaxyId = focused.slice(7);
    if ((motions.current.get(galaxyId)?.detail || 0) < .98) return;
    const topicLabel = labels.find(label => !label.category && label.interactive && props.topics.find(t => t.id === label.id)?.categoryId === galaxyId);
    if (topicLabel) buttons.current.get(topicLabel.id)?.focus({ preventScroll: true });
  }, [labels, focused, props.topics]);
  const labelsVisible = props.active && props.visibleTopics.length > 0;
  return <div ref={root} className={`cloud-universe ${props.active ? '' : 'scene-inactive'}`}>
    <SceneBoundary onFailure={props.onFailure}>
      <Canvas frameloop="demand" dpr={[1, 1.5]} camera={initialCamera} gl={defaults => {
        try { return new WebGLRenderer({ ...defaults, antialias: true, alpha: true }); }
        catch (error) { queueMicrotask(props.onFailure); throw error; }
      }} fallback={<p>Use List to explore topics when 3D is unavailable.</p>} onCreated={({ gl }) => { gl.setClearColor('#080D19', 0); }}>
        <CameraRig {...props} scene={scene} clouds={clouds} hovered={hovered} focused={focused} reduced={reduced} command={command} publish={publish} galaxies={galaxies} motions={motions.current} approach={approach} breathing={!paused && !reduced} obstacles={obstacles} labelSizes={labelSizes} />
        {galaxies.filter(g => g.matchingTopics > 0).map(galaxy => <GalaxyVisual key={galaxy.id} galaxy={galaxy} motion={motions.current.get(galaxy.id)!}
          count={particleBudget(scene.length)} selectedId={props.selectedId} hovered={hovered} active={props.active}
          onHover={setHovered} onApproach={id => approach.current(id)} onSelect={(id, canvas) => props.onSelect(id, buttons.current.get(id) || canvas)} />)}
      </Canvas>
    </SceneBoundary>
    <div className="cloud-labels" aria-label="Topics grouped by category" hidden={!labelsVisible}>
      {labels.map(label => label.category ? <button key={label.id} className="galaxy-label" data-galaxy={label.id} data-label-key={`galaxy:${label.id}`}
        style={{ left: label.x, top: label.y, color: galaxyColor(label.text || ''), opacity: label.opacity, pointerEvents: label.interactive ? 'auto' : 'none' }}
        tabIndex={label.interactive ? 0 : -1} aria-hidden={!label.interactive}
        aria-label={`Explore ${label.text} galaxy, ${label.count} topics, ${label.memories} memories${label.matching !== label.count ? `, ${label.matching} matching ${label.matching === 1 ? 'topic' : 'topics'}` : ''}`}
        onFocus={() => setFocused(`galaxy:${label.id}`)} onBlur={() => setFocused(null)} onClick={() => approach.current(label.id)}>
        <span className="galaxy-eyebrow">GALAXY</span><span className="galaxy-name">{label.text}</span>
        <span className="galaxy-totals">{label.count} topics · {label.memories} memories</span>
        {label.matching !== label.count && <span className="galaxy-matches">{label.matching} matching {label.matching === 1 ? 'topic' : 'topics'}</span>}
      </button> : (() => {
        const topic = props.topics.find(t => t.id === label.id); if (!topic) return null;
        const update = props.updates.find(u => u.topicId === topic.id);
        return <button key={topic.id} data-label-key={`topic:${topic.id}`} ref={e => { if (e) buttons.current.set(topic.id, e); else buttons.current.delete(topic.id); }} className={`cloud-label ${props.selectedId === topic.id ? 'selected' : ''}`}
          tabIndex={label.interactive ? 0 : -1} aria-hidden={!label.interactive}
          style={{ left: label.x, top: label.y, opacity: label.opacity, pointerEvents: label.interactive ? 'auto' : 'none', borderColor: props.selectedId === topic.id ? colorFor(topic) : undefined }}
          aria-label={`${topic.name}, ${topic.category}, ${topic.memoryCount} ${topic.memoryCount === 1 ? 'memory' : 'memories'}`} aria-pressed={props.selectedId === topic.id}
          onFocus={() => setFocused(topic.id)} onBlur={() => setFocused(null)} onPointerEnter={() => setHovered(topic.id)} onPointerLeave={() => setHovered(null)}
          onClick={e => props.onSelect(topic.id, e.currentTarget)}>
          <span className="cloud-name">{topic.name}</span><span className="cloud-meta">{topic.memoryCount} {topic.memoryCount === 1 ? 'memory' : 'memories'}{update && <span className="cloud-update">{update.label}</span>}</span>
        </button>;
      })())}
    </div>
    {props.active && props.topics.length > 0 && <>
      <nav className="scene-navigation" aria-label="Camera controls" data-scene-obstacle>
        <div className="zoom-capsule">
          <IconControl label="Zoom in" onClick={() => command.current('in')}><Plus size={20} aria-hidden="true" /></IconControl>
          <IconControl label="Zoom out" onClick={() => command.current('out')}><Minus size={20} aria-hidden="true" /></IconControl>
        </div>
        <IconControl label="Reset view" onClick={() => command.current('reset')}><RotateCcw size={18} aria-hidden="true" /></IconControl>
        <IconControl label={paused || reduced ? 'Resume animation' : 'Pause animation'} disabled={reduced}
          explanation={reduced ? 'Animation is off because reduced motion is enabled' : undefined} onClick={() => setPaused(value => !value)}>
          {paused || reduced ? <Play size={18} aria-hidden="true" /> : <Pause size={18} aria-hidden="true" />}
        </IconControl>
        <IconControl label="Help" ref={props.helpButtonRef} aria-expanded={props.helpOpen} aria-controls="exploration-help" onClick={props.onHelpToggle}><CircleHelp size={20} aria-hidden="true" /></IconControl>
      </nav>
      {props.helpOpen && <section className="help-popover" id="exploration-help" aria-label="Exploration help" data-scene-obstacle>
        <button className="icon-button popover-close" aria-label="Close help" onClick={props.onHelpClose}><X size={18} aria-hidden="true" /></button>
        <h2>Explore your galaxies</h2>
        <p>Select a galaxy to reveal topics. Select a topic to read its memories and original sources.</p>
        <dl><dt>Orbit</dt><dd>Drag · Arrow keys</dd><dt>Pan</dt><dd>Shift/right-drag · Shift + arrows</dd><dt>Zoom</dt><dd>Scroll/pinch · + / −</dd><dt>Reset</dt><dd>Reset view · Home</dd></dl>
        <p>Keyboard camera controls work when the scene has focus.</p>
        <p>Particles are visual texture, not individual memories. Topic size reflects saved memories; perspective also affects apparent size.</p>
        <p>Use List to browse every topic and exact count. {labels.filter(l => !l.category && l.interactive).length} of {props.visibleTopics.length} topic labels are currently visible.</p>
        <p>Pause animation stops the glow cycle. Reduced motion makes navigation immediate.</p>
      </section>}
    </>}

  </div>;
}

type RigProps = Props & { obstacles: Rect[]; labelSizes: LabelSizes; scene: SceneTopic[]; clouds: SceneTopic[]; hovered: string | null; focused: string | null; reduced: boolean; command: MutableRefObject<(command: Command) => void>; publish: (labels: Label[]) => void; galaxies: SceneGalaxy[]; motions: Map<string, Motion>; breathing: boolean; approach: MutableRefObject<(id: string) => void> };
function CameraRig(props: RigProps) {
  const { camera: rawCamera, gl, size, invalidate } = useThree();
  const camera = rawCamera as PerspectiveCamera;
  const controls = useRef<OrbitControls | null>(null);
  const latest = useRef(props); latest.current = props;
  const sizeRef = useRef(size); sizeRef.current = size;
  const tween = useRef(createCameraTransition());
  const offset = useRef(0);
  const offsetTween = useRef<{ from: number; to: number; start: number; duration: number } | null>(null);
  const initialized = useRef(false);
  const lastSelection = useRef<string | null>(null);
  const bounds = () => {
    const box = new Box3();
    for (const t of latest.current.scene) { const c = new Vector3(...t.center); box.expandByPoint(c.clone().addScalar(t.radius)); box.expandByPoint(c.clone().addScalar(-t.radius)); }
    return box.isEmpty() ? new Sphere(new Vector3(), 30) : box.getBoundingSphere(new Sphere());
  };
  const applyOffset = () => {
    const { width, height } = sizeRef.current;
    camera.setViewOffset(width, height, offset.current, 0, width, height); camera.updateProjectionMatrix();
  };
  const moveTo = (position: Vector3, target: Vector3, animated: boolean) => {
    const control = controls.current; if (!control) return;
    control.enableDamping = false; control.update();
    const now = performance.now(); const duration = animated && !latest.current.reduced ? 450 : 0;
    tween.current.begin({ position: camera.position.toArray() as Vec3, target: control.target.toArray() as Vec3 }, { position: position.toArray() as Vec3, target: target.toArray() as Vec3 }, now, duration);
    const panel = latest.current.selectedId && !latest.current.compact ? (sizeRef.current.width >= 1280 ? 512 : 400) + 24 : 0;
    offsetTween.current = { from: offset.current, to: panel / 2, start: now, duration };
    invalidate();
  };
  const reset = (animated = true) => {
    const sphere = bounds(); const panel = latest.current.selectedId && !latest.current.compact ? (sizeRef.current.width >= 1280 ? 512 : 400) + 48 : 0;
    const safeAspect = Math.max(.35, (sizeRef.current.width - panel) / sizeRef.current.height);
    const direction = new Vector3(.45, .4, 1).normalize();
    const right = new Vector3().crossVectors(new Vector3(0,1,0), direction).normalize();
    const up = new Vector3().crossVectors(direction, right).normalize();
    const tangent = Math.tan(camera.fov * Math.PI / 360);
    let distance = 65;
    for (const cloud of latest.current.scene) {
      const delta = new Vector3(...cloud.center).sub(sphere.center);
      const depth = delta.dot(direction);
      distance = Math.max(distance, (Math.abs(delta.dot(right)) + cloud.radius) / (tangent * safeAspect) + depth + cloud.radius,
        (Math.abs(delta.dot(up)) + cloud.radius) / tangent + depth + cloud.radius);
    }
    distance *= 1.2;
    for (const galaxy of latest.current.galaxies) {
      distance = Math.max(distance, galaxy.radius * 5.2 + new Vector3(...galaxy.center).distanceTo(sphere.center));
    }
    moveTo(sphere.center.clone().add(direction.multiplyScalar(distance)), sphere.center, animated);
  };
  const interrupt = () => { tween.current.cancel(); offsetTween.current = null; if (controls.current) controls.current.enableDamping = !latest.current.reduced; };
  useEffect(() => {
    const canvas = gl.domElement; const control = new OrbitControls(camera, canvas); controls.current = control;
    control.enableDamping = !latest.current.reduced; control.dampingFactor = .1; control.zoomToCursor = true;
    control.minDistance = 12; control.maxDistance = 2000; control.minPolarAngle = .08; control.maxPolarAngle = Math.PI - .08;
    const change = () => invalidate(); const start = () => interrupt();
    control.addEventListener('change', change); control.addEventListener('start', start);
    const lost = (event: Event) => { event.preventDefault(); latest.current.onFailure(); };
    const key = (event: KeyboardEvent) => {
      if (!latest.current.active || event.target !== canvas) return;
      const keys = ['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-','_','Home']; if (!keys.includes(event.key)) return;
      event.preventDefault(); interrupt();
      const direction = event.key === 'ArrowLeft' || event.key === 'ArrowUp' ? 1 : -1;
      if (event.key === 'Home') reset();
      else if (['+','='].includes(event.key)) control.dollyIn(.8);
      else if (['-','_'].includes(event.key)) control.dollyOut(.8);
      else if (event.shiftKey) control.pan(event.key === 'ArrowLeft' || event.key === 'ArrowRight' ? direction * 35 : 0, event.key === 'ArrowUp' || event.key === 'ArrowDown' ? direction * 35 : 0);
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') control.rotateLeft(direction * .12);
      else control.rotateUp(direction * .12);
      invalidate();
    };
    canvas.tabIndex = 0; canvas.setAttribute('aria-label','3D topic clouds. Arrow keys orbit; Shift and arrows pan; plus and minus zoom; Home resets. Use List to browse every topic.');
    canvas.addEventListener('keydown', key); canvas.addEventListener('webglcontextlost', lost);
    const lossTimer = contextLossFixture ? window.setTimeout(() => gl.getContext().getExtension('WEBGL_lose_context')?.loseContext(), 1500) : undefined;
    props.approach.current = id => {
      const galaxy = latest.current.galaxies.find(g => g.id === id); if (!galaxy) return;
      interrupt();
      const target = new Vector3(...galaxy.center), direction = camera.position.clone().sub(control.target).normalize();
      moveTo(target.clone().add(direction.multiplyScalar(galaxy.radius * 2.8)), target, true);
    };
    props.command.current = c => { interrupt(); if (c === 'reset') reset(); else if (c === 'in') control.dollyIn(.8); else control.dollyOut(.8); invalidate(); };
    invalidate();
    return () => { if (lossTimer) clearTimeout(lossTimer); control.dispose(); controls.current = null; tween.current.cancel(); canvas.removeEventListener('keydown', key); canvas.removeEventListener('webglcontextlost', lost); };
  }, [camera, gl, invalidate]);
  useEffect(() => {
    if (controls.current) { controls.current.enabled = props.active; controls.current.enableDamping = !props.reduced; }
    gl.domElement.tabIndex = props.active ? 0 : -1;
    gl.domElement.setAttribute('aria-hidden', String(!props.active));
    if (props.reduced && controls.current) {
      const end = tween.current.sample(Infinity);
      if (end) { camera.position.fromArray(end.position); controls.current.target.fromArray(end.target); }
      if (offsetTween.current) { offset.current = offsetTween.current.to; offsetTween.current = null; applyOffset(); }
      controls.current.update();
    }
    if (!props.active) interrupt();
    invalidate();
  }, [props.active, props.reduced, invalidate, camera, gl]);
  useEffect(() => {
    offset.current = Math.min(offset.current, props.compact ? 0 : (size.width >= 1280 ? 536 : 424) / 2);
    applyOffset(); invalidate();
  }, [size.width, size.height, props.compact, invalidate]);
  useEffect(() => {
    if (!props.scene.length || !controls.current) return;
    const sphere = bounds(); controls.current.maxDistance = Math.max(500, sphere.radius * 12);
    if (!initialized.current) { initialized.current = true; reset(false); }
    if (props.active && props.selectedId && props.selectedId !== lastSelection.current) {
      const cloud = props.scene.find(c => c.topic.id === props.selectedId);
      if (cloud) {
        const target = new Vector3(...cloud.center); const direction = camera.position.clone().sub(controls.current.target).normalize();
        moveTo(target.clone().add(direction.multiplyScalar(Math.max(35, cloud.radius * 7))), target, true);
        lastSelection.current = props.selectedId;
      }
    }
    if (!props.selectedId && lastSelection.current) {
      interrupt();
      // Drain OrbitControls inertia, then restore the exact pose at closure.
      const position = camera.position.clone(), target = controls.current.target.clone();
      controls.current.enableDamping = false; controls.current.update();
      camera.position.copy(position); controls.current.target.copy(target); controls.current.update();
      controls.current.enableDamping = !props.reduced; lastSelection.current = null;
    }
    invalidate();
  }, [props.scene, props.selectedId, props.active, invalidate]);
  useEffect(() => {
    let timer: number | undefined;
    let previous = performance.now();
    const sync = () => {
      if (timer !== undefined) clearInterval(timer);
      for (const motion of props.motions.values()) motion.breathing = props.breathing && props.active && !document.hidden;
      previous = performance.now();
      if (props.breathing && props.active && !document.hidden) timer = window.setInterval(() => {
        const now = performance.now();
        for (const motion of props.motions.values()) motion.elapsed += now - previous;
        previous = now; invalidate();
      }, Math.ceil(1000 / 30));
      invalidate();
    };
    sync(); document.addEventListener('visibilitychange', sync);
    return () => { clearInterval(timer); document.removeEventListener('visibilitychange', sync); };
  }, [props.breathing, props.active, props.motions, invalidate]);
  useEffect(() => { invalidate(); }, [props.obstacles, props.labelSizes, invalidate]);
  const labelSignature = useRef('');
  const geometrySignature = useRef('');
  const previousLabels = useRef<Label[]>([]);
  useFrame(() => {
    const control = controls.current; if (!control) return;
    const pose = tween.current.sample(performance.now());
    if (pose) { camera.position.fromArray(pose.position); control.target.fromArray(pose.target); if (!pose.done) invalidate(); else control.enableDamping = !latest.current.reduced; }
    const ot = offsetTween.current;
    if (ot) { const t = ot.duration ? Math.min(1, (performance.now() - ot.start) / ot.duration) : 1; const eased = t * t * (3 - 2 * t); offset.current = ot.from + (ot.to - ot.from) * eased; applyOffset(); if (t === 1) offsetTween.current = null; else invalidate(); }
    if (props.active && control.update()) invalidate();
    const sphere = bounds(); const displacement = control.target.clone().sub(sphere.center); const maxPan = Math.max(50, sphere.radius * 2);
    if (displacement.length() > maxPan) { const clamped = sphere.center.clone().add(displacement.setLength(maxPan)); camera.position.add(clamped.clone().sub(control.target)); control.target.copy(clamped); control.update(); }
    gl.domElement.dataset.cameraPosition = camera.position.toArray().map(n => n.toFixed(3)).join(',');
    gl.domElement.dataset.cameraTarget = control.target.toArray().map(n => n.toFixed(3)).join(',');
    gl.domElement.dataset.renderCount = String(Number(gl.domElement.dataset.renderCount || 0) + 1);
    gl.domElement.dataset.cloudCount = String(props.clouds.length);
    gl.domElement.dataset.particleCount = String(props.clouds.length * particleBudget(props.scene.length));
    gl.domElement.dataset.reducedMotion = String(props.reduced);
    if (!props.active || document.hidden) return;
    let changing = false;
    for (const galaxy of props.galaxies) {
      const motion = props.motions.get(galaxy.id)!;
      const target = galaxyDetail(camera.position.distanceTo(new Vector3(...galaxy.center)), galaxy.radius);
      motion.detail = motion.transition.update(target, performance.now(), props.reduced);
      motion.breathing = props.breathing;
      changing ||= !motion.transition.settled;
    }
    if (changing) invalidate();
    gl.domElement.dataset.galaxyDetails = props.galaxies.map(g => `${g.id}:${props.motions.get(g.id)!.detail.toFixed(3)}`).join(',');
    gl.domElement.dataset.breathing = String(props.breathing);
    // Breathing updates shader uniforms only. Stable labels do not trigger React work at 30fps.
    const geometry = [camera.matrixWorld.elements.join(','), camera.projectionMatrix.elements.join(','), props.clouds.map(c => `${c.topic.id}:${c.topic.name}:${c.topic.memoryCount}`).join('|'), props.galaxies.map(g => `${g.id}:${g.topicCount}:${g.memoryCount}:${props.motions.get(g.id)!.detail.toFixed(2)}`).join('|'), size.width, size.height, JSON.stringify(props.obstacles), JSON.stringify(props.labelSizes)].join(';');
    const signature = [geometry, props.focused, props.hovered, props.selectedId].join(';');
    if (signature === labelSignature.current) return;
    const stableLayout = geometry === geometrySignature.current;
    geometrySignature.current = geometry;
    labelSignature.current = signature;
    const { width, height } = size;
    const edge = width < 620 ? 16 : 24;
    const project = (center: Vec3) => { const p = new Vector3(...center).project(camera); return { x: (p.x + 1) * width / 2, y: (1 - p.y) * height / 2, z: p.z }; };
    const categoryOf = new Map(props.galaxies.flatMap(g => g.topics.map(c => [c.topic.id, g] as const)));
    const candidates = props.clouds.map(c => {
      const galaxy = categoryOf.get(c.topic.id)!; const detail = props.motions.get(galaxy.id)!.detail;
      const center = c.center.map((v, i) => galaxy.center[i] + (v - galaxy.center[i]) * detail) as Vec3;
      return { cloud: c, p: project(center), detail, distance: camera.position.distanceTo(new Vector3(...center)), priority: c.topic.id === props.focused ? 4 : c.topic.id === props.selectedId ? 3 : c.topic.id === props.hovered ? 1 : 0 };
    });
    candidates.sort((a,b) => b.priority - a.priority || a.distance - b.distance);
    const output: Label[] = [];
    const { place } = createLabelPlacer({ x: edge, y: edge, w: width-edge*2, h: height-edge*2 }, props.obstacles);
    const topicsToPlace = (priorityOnly: boolean) => {
      for (const { cloud, p, detail, priority } of candidates) {
        if ((priority > 1) !== priorityOnly || output.filter(l => !l.category).length >= 16 || ((p.z < -1 || p.z > 1 || detail < .02) && priority < 2)) continue;
        const previous = stableLayout && previousLabels.current.find(l => !l.category && l.id === cloud.topic.id);
        const placements = [...(previous ? [[previous.x, previous.y]] : []), [p.x + 18,p.y + 14],[p.x - 202,p.y + 14],[p.x + 18,p.y - 104],[p.x - 202,p.y - 104]];
        for (const [px, py] of placements) {
          const labelSize = props.labelSizes[`topic:${cloud.topic.id}`] || { w: 184, h: 114 };
          const rect = place(px, py, labelSize.w, labelSize.h, priority >= 2); if (!rect) continue;
          output.push({ id: cloud.topic.id, x: rect.x, y: rect.y, opacity: priority >= 2 ? 1 : Math.min(1,Math.round(detail*200)/100), interactive: detail >= .5 || priority >= 2 }); break;
        }
      }
    };
    topicsToPlace(true);
    for (const galaxy of props.galaxies) {
      if (!galaxy.matchingTopics) continue;
      const detail = props.motions.get(galaxy.id)!.detail, focused = props.focused === `galaxy:${galaxy.id}`;
      if (detail > .98 && !focused) continue;
      const p = project(galaxy.center);
      if (p.z < -1 || p.z > 1) continue;
      const labelHeight = props.labelSizes[`galaxy:${galaxy.id}`]?.h || (galaxy.matchingTopics !== galaxy.topicCount ? 168 : 144);
      const previous = stableLayout && previousLabels.current.find(l => l.category && l.id === galaxy.id);
      const rect = (previous && place(previous.x,previous.y,224,labelHeight)) || place(p.x-112,p.y+50,224,labelHeight)
        || place(p.x-112,p.y-labelHeight-60,224,labelHeight)
        || place(p.x+70,p.y-labelHeight/2,224,labelHeight)
        || place(p.x-294,p.y-labelHeight/2,224,labelHeight)
        || place(p.x-112,p.y+50,224,labelHeight, true);
      if (rect) output.push({ id: galaxy.id, x: rect.x, y: rect.y, category: true, text: galaxy.name, count: galaxy.topicCount, memories: galaxy.memoryCount, matching: galaxy.matchingTopics, opacity: focused ? 1 : Math.min(1,Math.round((1-detail)*200)/100), interactive: detail < .5 || focused });
    }
    topicsToPlace(false);
    previousLabels.current = output;
    props.publish(output);
  });
  return null;
}
