/**
 * Utilitário de conversão de unidades de resistência elétrica.
 * Usado pela Calculadora de Resistência e pelos formulários de
 * Resistência de Contato (Disjuntor MT/BT, Seccionadora), que
 * permitem ao técnico medir em µΩ ou mΩ.
 *
 * Unidade de referência interna: Ohm (Ω)
 */
const FATORES_RESISTENCIA = {
  'µΩ': 1e-6,
  'mΩ': 1e-3,
  'Ω':  1,
  'kΩ': 1e3,
  'MΩ': 1e6,
  'GΩ': 1e9
};

/**
 * Converte um valor de uma unidade de resistência para outra.
 * @param {number} valor - valor numérico a converter
 * @param {string} deUnidade - unidade de origem (chave de FATORES_RESISTENCIA)
 * @param {string} paraUnidade - unidade de destino (chave de FATORES_RESISTENCIA)
 * @returns {number|null} valor convertido, ou null se entrada inválida
 */
function converterResistencia(valor, deUnidade, paraUnidade) {
  if (valor === null || valor === undefined || valor === '' || isNaN(valor)) return null;
  if (!(deUnidade in FATORES_RESISTENCIA) || !(paraUnidade in FATORES_RESISTENCIA)) return null;
  const valorEmOhms = parseFloat(valor) * FATORES_RESISTENCIA[deUnidade];
  return valorEmOhms / FATORES_RESISTENCIA[paraUnidade];
}

/**
 * Atalho usado pelos formulários de resistência de contato para
 * normalizar sempre em microOhms (µΩ) antes de enviar ao backend,
 * já que o banco armazena um único valor numérico sem unidade.
 */
function paraMicroOhms(valor, deUnidade) {
  return converterResistencia(valor, deUnidade, 'µΩ');
}
