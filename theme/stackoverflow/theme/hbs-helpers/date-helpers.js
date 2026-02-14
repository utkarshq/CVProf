const moment = require('moment');

const dateHelpers = {
  MY: date => {
    if (!date || date === 'Present' || date === 'Current') return 'Present';
    const m = moment(date.toString(), ['YYYY-MM-DD', 'YYYY-MM', 'YYYY']);
    return m.isValid() ? m.format('MMM YYYY') : date;
  },
  Y: date => {
    if (!date || date === 'Present' || date === 'Current') return 'Present';
    const m = moment(date.toString(), ['YYYY-MM-DD', 'YYYY-MM', 'YYYY']);
    return m.isValid() ? m.format('YYYY') : date;
  },
  DMY: date => {
    if (!date || date === 'Present' || date === 'Current') return 'Present';
    const m = moment(date.toString(), ['YYYY-MM-DD']);
    return m.isValid() ? m.format('D MMM YYYY') : date;
  }
};

module.exports = { dateHelpers };
