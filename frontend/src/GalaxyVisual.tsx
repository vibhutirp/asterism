import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { AdditiveBlending, BufferAttribute, BufferGeometry, Color, Mesh, ShaderMaterial, Vector3 } from 'three';
import { aggregateParticles, glowBrightness } from './galaxy-model.ts';
import type { SceneGalaxy } from './galaxy-model.ts';
import { cloudParticles } from './scene-model.ts';
import type { SceneTopic } from './scene-model.ts';

export type GalaxyMotion = { detail: number; elapsed: number; breathing: boolean };
export const galaxyColor = (name: string) => name.toLowerCase() === 'personal' ? '#7DDECA' : '#83B8FF';

/** One set of points per topic, with two positions interpolated entirely on the GPU. */
function MorphingTopic({ cloud, galaxy, motion, count, selected, highlighted, active, onHover, onSelect }: {
  cloud: SceneTopic; galaxy: SceneGalaxy; motion: GalaxyMotion; count: number;
  selected: boolean; highlighted: boolean; active: boolean;
  onHover: (id: string | null) => void; onSelect: (id: string, canvas: HTMLCanvasElement) => void;
}) {
  const { gl } = useThree();
  const hit = useRef<Mesh>(null);
  const material = useRef<ShaderMaterial>(null);
  const geometry = useMemo(() => {
    const local = cloudParticles(cloud.topic.id, count);
    const detail = local.map((v, i) => v * cloud.radius + cloud.center[i % 3] - galaxy.center[i % 3]);
    const geometry = new BufferGeometry();
    geometry.setAttribute('position', new BufferAttribute(aggregateParticles(cloud.topic.id, count, galaxy.radius), 3));
    geometry.setAttribute('aDetailPosition', new BufferAttribute(detail, 3));
    geometry.setAttribute('aSize', new BufferAttribute(Float32Array.from({ length: count }, (_, i) => 1.6 + Math.abs(local[i * 3]) * 2), 1));
    return geometry;
  }, [cloud.topic.id, cloud.radius, ...cloud.center, ...galaxy.center, galaxy.radius, count]);
  useEffect(() => () => geometry.dispose(), [geometry]);
  const uniforms = useMemo(() => ({ uColor: { value: new Color(galaxyColor(galaxy.name)) }, uBrightness: { value: 1 }, uDetail: { value: 0 }, uDpr: { value: gl.getPixelRatio() } }), [galaxy.name, gl]);
  useFrame(() => {
    if (material.current) {
      material.current.uniforms.uDetail.value = motion.detail;
      material.current.uniforms.uDpr.value = gl.getPixelRatio();
      material.current.uniforms.uBrightness.value = (selected ? 1.25 : highlighted && motion.detail >= .5 ? 1.15 : .85) * (motion.breathing ? glowBrightness(motion.elapsed, cloud.seed) : 1);
      gl.domElement.dataset.glowBrightness = material.current.uniforms.uBrightness.value.toFixed(5);
    }
    if (hit.current) {
      hit.current.position.set(...cloud.center).sub(new Vector3(...galaxy.center)).multiplyScalar(motion.detail);
      hit.current.visible = active && motion.detail >= .5;
    }
  });
  return <>
    <points geometry={geometry} raycast={() => {}} frustumCulled={false}>
      <shaderMaterial ref={material} transparent depthWrite={false} blending={AdditiveBlending} uniforms={uniforms}
        vertexShader={`attribute float aSize; attribute vec3 aDetailPosition; uniform float uDpr; uniform float uDetail;
          void main() { vec4 p = modelViewMatrix * vec4(mix(position,aDetailPosition,uDetail),1.0); gl_Position = projectionMatrix * p;
          gl_PointSize = clamp(aSize * uDpr * 420.0 / max(1.0,-p.z),2.0*uDpr,20.0*uDpr); }`}
        fragmentShader={`uniform vec3 uColor; uniform float uBrightness; void main() {
          float d=length(gl_PointCoord-vec2(0.5))*2.0; if(d>1.0) discard;
          float halo=pow(1.0-d,1.8); float core=1.0-smoothstep(0.0,0.35,d);
          gl_FragColor=vec4(mix(uColor,vec3(0.94,0.98,1.0),core*.75),min(1.0,(halo+core*.35)*uBrightness));
          #include <colorspace_fragment>
        }`} />
    </points>
    <mesh ref={hit} scale={cloud.radius * 1.08}
      onPointerOver={e => { if (active && motion.detail >= .5) { e.stopPropagation(); onHover(cloud.topic.id); } }}
      onPointerOut={() => onHover(null)}
      onClick={e => { if (active && motion.detail >= .5 && e.delta <= 5) { e.stopPropagation(); onSelect(cloud.topic.id, gl.domElement); } }}>
      <sphereGeometry args={[1, 16, 12]} /><meshBasicMaterial transparent opacity={0} depthWrite={false} />
    </mesh>
  </>;
}

export default function GalaxyVisual({ galaxy, motion, count, selectedId, hovered, active, onHover, onSelect, onApproach }: {
  galaxy: SceneGalaxy; motion: GalaxyMotion; count: number; selectedId: string | null; hovered: string | null; active: boolean;
  onHover: (id: string | null) => void; onSelect: (id: string, canvas: HTMLCanvasElement) => void; onApproach: (id: string) => void;
}) {
  const atmosphere = useRef<Mesh>(null), hit = useRef<Mesh>(null);
  const personal = galaxy.name.toLowerCase() === 'personal';
  const uniforms = useMemo(() => ({ uInner: { value: new Color(personal ? '#00BDCD' : '#3164DA') }, uOuter: { value: new Color(personal ? '#165F91' : '#6930A3') } }), [personal]);
  useFrame(({ camera }) => {
    // A billboard stays anchored in world space while presenting a soft volume from every angle.
    atmosphere.current?.quaternion.copy(camera.quaternion);
    if (hit.current) hit.current.visible = active && motion.detail < .5;
  });
  return <group position={galaxy.center}>
    <mesh ref={atmosphere} scale={[galaxy.radius * 5.6, galaxy.radius * 4.2, 1]} renderOrder={-10} raycast={() => {}}>
      <planeGeometry args={[1, 1]} />
      <shaderMaterial transparent depthWrite={false} depthTest={false} blending={AdditiveBlending} uniforms={uniforms}
        vertexShader={`varying vec2 vUv; void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`}
        fragmentShader={`varying vec2 vUv; uniform vec3 uInner; uniform vec3 uOuter;
          void main(){vec2 p=(vUv-.5)*2.0; float r=length(p); float edge=1.0-smoothstep(.45,1.0,r);
          float angle=atan(p.y,p.x); float wisps=.72+.28*sin(angle*2.0-r*10.0+p.x*3.0);
          float core=exp(-dot(p*vec2(1.05,1.7),p*vec2(1.05,1.7))*5.0);
          float outer=exp(-r*r*3.2)*wisps;
          gl_FragColor=vec4(mix(uOuter,uInner,core),edge*(outer*.27+core*.20));
          #include <colorspace_fragment>
        }`} />
    </mesh>
    {galaxy.topics.filter(c => c.radius > 0).map(cloud => <MorphingTopic key={cloud.topic.id} {...{ cloud, galaxy, motion, count, active, onHover, onSelect }} selected={cloud.topic.id === selectedId} highlighted={cloud.topic.id === hovered} />)}
    <mesh ref={hit} scale={[galaxy.radius * .64, galaxy.radius * .5, galaxy.radius * .6]}
      onClick={e => { if (active && motion.detail < .5 && e.delta <= 5) { e.stopPropagation(); onApproach(galaxy.id); } }}>
      <sphereGeometry args={[1, 20, 16]} /><meshBasicMaterial transparent opacity={0} depthWrite={false} />
    </mesh>
  </group>;
}
