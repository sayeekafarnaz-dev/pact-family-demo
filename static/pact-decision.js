(() => {
  const dollars = new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0,
  });
  const percent = value => `${(value * 100).toFixed(1)}%`;
  const amount = value => dollars.format(value);

  async function request(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Decision Lab unavailable.');
    return data;
  }

  window.PACT_ANALYTICS.decision = async function () {
    const host = document.getElementById('packd-decision-lab');
    if (!host) return;
    host.innerHTML = `
      <h1>Decision Lab</h1>
      <p>Compare one person's life event with the Morgan family's baseline using the same synthetic market paths.</p>
      <section class="card">
        <form>
          <label>Life event <select name="event" required></select></label>
          <label>Family member <select name="member" required></select></label>
          <div hidden><label>One-time cost (USD) <input name="amount" type="number" min="1" max="1000000" value="10000"></label></div>
          <button type="submit" disabled>Compare family outcomes</button>
        </form>
      </section>
      <div aria-live="polite"></div>`;
    const form = host.querySelector('form');
    const output = host.querySelector('[aria-live]');
    const event = form.elements.event;
    const member = form.elements.member;
    const cost = form.elements.amount;
    const run = form.querySelector('button');
    try {
      const options = await request('/api/public/decision/options');
      for (const [id, label] of Object.entries(options.events)) event.add(new Option(label, id));
      for (const item of options.members) member.add(new Option(item.name, item.id));
      run.disabled = false;
    } catch (error) {
      output.textContent = error.message;
      return;
    }
    const hasCost = () => ['education', 'major_purchase'].includes(event.value);
    event.addEventListener('change', () => {
      cost.closest('div').hidden = !hasCost();
      cost.required = hasCost();
    });
    form.addEventListener('submit', async submission => {
      submission.preventDefault();
      run.disabled = true;
      output.textContent = 'Running paired simulations…';
      try {
        const result = await request('/api/public/decision', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({event: event.value, member_id: member.value, amount: hasCost() ? cost.valueAsNumber : 0}),
        });
        output.innerHTML = `
          <section class="grid">
            <div class="card"><h3>Baseline median</h3><div class="metric">${amount(result.before.terminal_median)}</div></div>
            <div class="card"><h3>After the event</h3><div class="metric">${amount(result.after.terminal_median)}</div></div>
            <div class="card"><h3>Estimated change</h3><div class="metric">${amount(result.family_terminal_change)}</div></div>
          </section>
          <section class="card">
            <h2>Individual risk capacity</h2>
            <div class="decision-members"></div>
            <p>Optimised family volatility: ${percent(result.optimisation.before_family_volatility)} → ${percent(result.optimisation.after_family_volatility)}</p>
            <p class="hint">${result.methodology.paths.toLocaleString('en-US')} paired paths over ${result.methodology.years} years. Synthetic scenario, not a forecast.</p>
          </section>`;
        const rows = output.querySelector('.decision-members');
        for (const person of result.members) {
          const row = document.createElement('p');
          row.textContent = `${person.name}: ${percent(person.before_risk_capacity)} → ${percent(person.scenario_risk_capacity)}`;
          rows.appendChild(row);
        }
      } catch (error) {
        output.textContent = error.message;
      } finally {
        run.disabled = false;
      }
    });
  };
})();
