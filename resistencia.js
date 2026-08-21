/** Portal de Ensaios — conversão de unidades de resistência. */
const FATORES_RESISTENCIA = {
  'µΩ': 1e-6,
  'mΩ': 1e-3,
  'Ω': 1,
  'kΩ': 1e3,
  'MΩ': 1e6,
  'GΩ': 1e9,
  'TΩ': 1e12
};

function converterResistencia(valor, deUnidade, paraUnidade) {
  if (valor === null || valor === undefined || valor === '' || Number.isNaN(Number(valor))) return null;
  if (!(deUnidade in FATORES_RESISTENCIA) || !(paraUnidade in FATORES_RESISTENCIA)) return null;
  const valorEmOhms = Number(valor) * FATORES_RESISTENCIA[deUnidade];
  return valorEmOhms / FATORES_RESISTENCIA[paraUnidade];
}

function paraMicroOhms(valor, deUnidade) {
  return converterResistencia(valor, deUnidade, 'µΩ');
}
