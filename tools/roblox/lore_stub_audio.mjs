const P = new Proxy(function () {}, { get: (t, k) => (k === Symbol.toPrimitive ? () => 0 : k === 'then' ? undefined : P), apply: () => P });
export const sfx = P, synth = P, hrLevel = P, audio = P, audioOut = P, encSfx = P, eruptRumble = P, hum = P, initAudio = P, laserWhine = P,
  loopLevel = P, loopSfx = P, rainLoop = P, setListener = P, setMuffle = P, setVolume = P, shredMotor = P, stopLoops = P, trickle = P, windLoop = P;
export default P;
