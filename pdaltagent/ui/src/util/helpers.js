export const stringifyExpression = (expr) => {
  if (typeof expr === 'object') {
    if (Object.keys(expr).length === 1) {
      const operator = Object.keys(expr)[0];
      if (['AND', 'OR'].includes(operator)) {
        return '(' + expr[operator].map((op) => stringifyExpression(op)).join(` ${operator} `) + ')';
      }
      if (['IN', 'NOT IN'].includes(operator)) {
        const left = expr[operator][0];
        const right = '[' + expr[operator][1].map((op) => stringifyExpression(op)).join(', ') + ']';
        return `${left} ${operator} ${right}`;
      }
      if (['=', '!='].includes(operator)) {
        const left = expr[operator][0];
        const right = stringifyExpression(expr[operator][1]);
        return `${left} ${operator} ${right}`;
      }
      throw new Error(`Unknown operator: ${operator}`);
    } else if (
      Object.keys(expr).length === 2 &&
      ['formal-regex', 'regex'].includes(expr.type) &&
      'value' in expr
    ) {
      if (expr.type === 'formal-regex') {
        return `/${expr.value}/`;
      } else if (expr.type === 'regex') {
        return `"${expr.value}"`;
      }
    } else {
      throw new Error(`Unknown expression: ${JSON.stringify(expr)}`);
    }
  } else if (typeof expr === 'string') {
    return `"${expr}"`;
  } else {
    throw new Error(`Unknown expression: ${expr}`);
  }
};

export const formatLocalShortDate = (ts) => {
  const date = new Date(ts * 1000);
  const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
  return date.toLocaleString(undefined, options);
}

export const secondsToHuman = (seconds) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${days}d ${hours}h ${minutes}m ${secs}s`;
}

export const urlFor = (path) => {
  return `${window.location.origin}${path}`;
}