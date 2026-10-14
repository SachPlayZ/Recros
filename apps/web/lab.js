const el = (id) => document.getElementById(id);
const text = (tag, value, className) => {
  const node = document.createElement(tag); node.textContent = value;
  if (className) node.className = className;
  return node;
};
let catalog;
let request = 0;
async function show() {
  const generation = ++request;
  const seed = catalog.items.find((i) => i.id === el('seed').value);
  el('source').replaceChildren(text('h2', seed.title), text('p', seed.description));
  if (seed.source_url) { const link = text('a', 'Summary source'); link.href = seed.source_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; el('source').append(link); }
  el('results').replaceChildren(text('p', 'Loading connections…'));
  const query = new URLSearchParams({ seed: seed.id, target: el('target').value });
  if (el('remove').value) query.set('remove', el('remove').value);
  try {
    const response = await fetch(`/api/lab/bridges?${query}`);
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    const data = await response.json();
    if (generation !== request) return;
    el('results').replaceChildren();
    for (const item of data.items) {
      const card = text('article', '');
      card.append(text('span', `${item.domain.toUpperCase()} · connection ${item.bridge_score.toFixed(2)}`, 'score'), text('h3', item.title), text('p', item.description));
      if (item.source_url) { const link = text('a', 'Summary source'); link.href = item.source_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; card.append(link); }
      if (!item.evidence.length) card.append(text('p', 'No supported shared theme. The system abstains from explaining a connection.', 'empty'));
      for (const evidence of item.evidence) {
        card.append(text('strong', evidence.concept), text('p', 'In your starting item:'), text('blockquote', evidence.source_quote), text('p', 'In this suggestion:'), text('blockquote', evidence.target_quote));
        const button = text('button', `Remove “${evidence.concept}”`);
        button.addEventListener('click', () => { el('remove').value = evidence.concept; show(); });
        card.append(button);
      }
      el('results').append(card);
    }
    el('model').textContent = `Model: ${data.model} · ${data.mode}`;
  } catch (error) { if (generation === request) el('results').replaceChildren(text('p', error.message)); }
}
async function init() {
  try {
    const response = await fetch('/api/lab/catalog');
    if (!response.ok) throw new Error('The annotation cache is missing. Run the documented annotation command first.');
    catalog = await response.json();
    for (const item of catalog.items) { const option = text('option', `${item.title} (${item.domain})`); option.value = item.id; el('seed').append(option); }
    const concepts = [...new Set(catalog.items.flatMap((i) => i.annotation.facets.map((f) => f.concept)))].sort();
    for (const concept of concepts) { const option = text('option', concept); option.value = concept; el('remove').append(option); }
    for (const id of ['target', 'remove']) el(id).addEventListener('change', show);
    el('seed').addEventListener('change', () => { el('remove').value = ''; show(); });
    await show();
  } catch (error) { el('results').replaceChildren(text('p', error.message)); }
}
init();
