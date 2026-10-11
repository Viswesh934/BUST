/**
 * Competitor Intelligence & Benchmarking Deliverable View
 * Renders a clean, structured comparison table and firmographics data.
 */

let compActiveTab: string = 'matrix';

export function renderCompetitorView(
	container: HTMLElement,
	art: any,
	dealContext: any,
	onRefreshCrustdata?: () => Promise<void>
): void {
	const comp = art.content || {};
	const rev = comp.revenue_intelligence || {};
	const matrix: Array<{ category: string; competitor: string; our_solution: string }> = comp.head_to_head_matrix || [];
	const vulns: string[] = comp.pricing_vulnerabilities || [];
	const traps: string[] = comp.landmine_traps || [];
	const crust = comp.crustdata_research || {};
	const crustRes = crust.research || null;

	const compName = comp.competitor_name || 'Incumbent';

	container.innerHTML = `
		<div class="space-y-3 min-w-0 break-words">
			<!-- TOP DOSSIER HEADER STRIP -->
			<div class="card bg-base-100 border border-base-300 p-3 rounded-xl shadow-2xs space-y-2 min-w-0 overflow-hidden">
				<div class="flex items-center justify-between border-b border-base-200 pb-2 gap-2">
					<div class="min-w-0">
						<span class="text-[10px] text-base-content/60 font-mono uppercase block truncate">${comp.market_category || 'Enterprise Software'}</span>
						<h4 class="font-bold text-sm text-base-content flex items-center gap-1.5 truncate">
							<span>${compName}</span>
							<span class="badge badge-xs badge-warning font-semibold shrink-0">Incumbent</span>
						</h4>
					</div>
					<div class="flex items-center gap-1 shrink-0">
						<span class="badge badge-xs font-mono font-bold ${rev.has_public_revenue ? 'badge-success' : 'badge-neutral'}">
							${rev.revenue_estimate || 'Private'}
						</span>
					</div>
				</div>

				<!-- SUB-TAB SWITCHER -->
				<div class="flex items-center gap-1 overflow-x-auto pb-0.5 no-scrollbar" id="comp-table-subtabs">
					<button type="button" class="btn btn-xs comp-tab-btn ${compActiveTab === 'matrix' ? 'btn-neutral' : 'btn-ghost'}" data-tab="matrix">
						⚔️ Matrix (${matrix.length})
					</button>
					<button type="button" class="btn btn-xs comp-tab-btn ${compActiveTab === 'metrics' ? 'btn-neutral' : 'btn-ghost'}" data-tab="metrics">
						📊 Firmographics
					</button>
					<button type="button" class="btn btn-xs comp-tab-btn ${compActiveTab === 'traps' ? 'btn-neutral' : 'btn-ghost'}" data-tab="traps">
						⚠️ Traps (${vulns.length})
					</button>
					<button type="button" class="btn btn-xs comp-tab-btn ${compActiveTab === 'landmines' ? 'btn-neutral' : 'btn-ghost'}" data-tab="landmines">
						💣 Questions (${traps.length})
					</button>
					${comp.displacement_playbook ? `
						<button type="button" class="btn btn-xs comp-tab-btn ${compActiveTab === 'playbook' ? 'btn-neutral' : 'btn-ghost'}" data-tab="playbook">
							🏆 Playbook
						</button>
					` : ''}
				</div>
			</div>

			<!-- 1. HEAD-TO-HEAD MATRIX TABLE -->
			<div id="comp-view-matrix" class="${compActiveTab === 'matrix' ? '' : 'hidden'} space-y-2 min-w-0">
				${matrix.length > 0 ? `
					<div class="overflow-x-auto rounded-xl border border-base-300 bg-base-100 shadow-2xs">
						<table class="table table-xs md:table-sm w-full">
							<thead class="bg-base-200/90 text-[10px] font-mono uppercase tracking-wider text-base-content/75 border-b border-base-300">
								<tr>
									<th class="w-1/4 py-2 px-2.5">Category</th>
									<th class="w-3/8 py-2 px-2.5 text-error font-bold">${compName}</th>
									<th class="w-3/8 py-2 px-2.5 text-success font-bold">Our Advantage</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-base-200 text-xs">
								${matrix.map((row) => `
									<tr class="hover:bg-base-200/30 transition-colors">
										<td class="align-top py-2 px-2.5 font-bold">
											<span class="badge badge-xs badge-neutral font-mono truncate max-w-[110px] inline-block">${row.category}</span>
										</td>
										<td class="align-top py-2 px-2.5 text-base-content/85 text-[11px] leading-relaxed break-words bg-error/5">
											${row.competitor}
										</td>
										<td class="align-top py-2 px-2.5 text-base-content font-medium text-[11px] leading-relaxed break-words bg-success/5">
											<span class="text-success font-bold mr-1">✓</span>${row.our_solution}
										</td>
									</tr>
								`).join('')}
							</tbody>
						</table>
					</div>
				` : `
					<div class="p-6 text-center text-xs text-base-content/60 bg-base-100 rounded-xl border border-base-300">
						No comparison matrix generated yet.
					</div>
				`}
			</div>

			<!-- 2. FIRMOGRAPHICS & CRUSTDATA TABLE -->
			<div id="comp-view-metrics" class="${compActiveTab === 'metrics' ? '' : 'hidden'} space-y-2 min-w-0">
				<div class="overflow-x-auto rounded-xl border border-base-300 bg-base-100 shadow-2xs">
					<table class="table table-xs md:table-sm w-full text-xs">
						<thead class="bg-base-200/90 text-[10px] font-mono uppercase tracking-wider text-base-content/75 border-b border-base-300">
							<tr>
								<th class="w-1/3 py-2 px-2.5">Dimension</th>
								<th class="py-2 px-2.5">Verified Intelligence</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-base-200 text-[11px]">
							<tr>
								<td class="font-mono text-base-content/60 py-2 px-2.5 align-top">Online Revenue</td>
								<td class="py-2 px-2.5 font-bold font-mono text-base-content break-words">
									${rev.revenue_estimate || 'Not publicly disclosed'} 
									<span class="badge badge-xs badge-outline font-normal ml-1">${rev.valuation_or_status || 'Private'}</span>
									${rev.source_note ? `<span class="block text-[10px] text-base-content/50 font-normal mt-0.5 truncate max-w-[260px]">${rev.source_note}</span>` : ''}
								</td>
							</tr>
							<tr>
								<td class="font-mono text-base-content/60 py-2 px-2.5 align-top">Pricing Model</td>
								<td class="py-2 px-2.5 font-medium text-base-content font-mono break-words">
									${comp.pricing_model || 'Usage-based'}
								</td>
							</tr>
							${crustRes ? `
								<tr>
									<td class="font-mono text-base-content/60 py-2 px-2.5 align-top">Headcount</td>
									<td class="py-2 px-2.5 text-base-content break-words">
										<span class="font-bold">${crustRes.headcount?.total_employees || '1,000+'}</span> 
										<span class="text-success font-semibold">(${crustRes.headcount?.yoy_growth_percentage || '+12%'})</span>
										<span class="block text-[10px] text-base-content/70 mt-0.5">${crustRes.headcount?.headcount_signal || 'Workforce active'}</span>
									</td>
								</tr>
								<tr>
									<td class="font-mono text-base-content/60 py-2 px-2.5 align-top">Valuation / Capital</td>
									<td class="py-2 px-2.5 text-base-content font-mono font-medium break-words">
										${crustRes.financials_and_funding?.valuation_or_market_cap || crustRes.financials_and_funding?.total_funding || 'Enterprise disclosure'}
									</td>
								</tr>
								${crustRes.hiring_signals ? `
									<tr>
										<td class="font-mono text-base-content/60 py-2 px-2.5 align-top">Hiring Signals</td>
										<td class="py-2 px-2.5 text-error font-medium leading-relaxed break-words bg-error/5">
											⚠️ ${crustRes.hiring_signals.strategic_vulnerability}
											<div class="flex flex-wrap gap-1 pt-1">
												${(crustRes.hiring_signals.critical_focus_areas || []).map((f: string) => `
													<span class="badge badge-xs badge-neutral truncate max-w-[130px] inline-block">${f}</span>
												`).join('')}
											</div>
										</td>
									</tr>
								` : ''}
								${crustRes.tech_stack_footprint?.length ? `
									<tr>
										<td class="font-mono text-base-content/60 py-2 px-2.5 align-top">Tech Stack</td>
										<td class="py-2 px-2.5">
											<div class="flex flex-wrap gap-1 max-w-full overflow-hidden">
												${crustRes.tech_stack_footprint.map((t: string) => `
													<span class="badge badge-xs badge-neutral font-mono truncate max-w-[110px] inline-block">${t}</span>
												`).join('')}
											</div>
										</td>
									</tr>
								` : ''}
							` : `
								<tr>
									<td class="font-mono text-base-content/60 py-2 px-2.5 align-top">Crustdata Status</td>
									<td class="py-2 px-2.5 text-base-content/70 italic">
										Click "Deep Research" below to query Crustdata B2B MCP for real-time firmographics.
									</td>
								</tr>
							`}
						</tbody>
					</table>
				</div>

				<div class="flex items-center justify-between text-[10px] px-1 pt-1">
					<span class="text-base-content/50 font-mono truncate max-w-[180px]">${crust.source || 'Crustdata B2B Platform'}</span>
					<button type="button" class="btn btn-xs btn-ghost gap-1 cursor-pointer" id="btn-run-crustdata-research">
						${crustRes ? '🔄 Refresh Crustdata' : '⚡ Deep Research (Crustdata)'}
					</button>
				</div>
			</div>

			<!-- 3. PRICING TRAPS TABLE -->
			<div id="comp-view-traps" class="${compActiveTab === 'traps' ? '' : 'hidden'} space-y-2 min-w-0">
				${vulns.length > 0 ? `
					<div class="overflow-x-auto rounded-xl border border-base-300 bg-base-100 shadow-2xs">
						<table class="table table-xs md:table-sm w-full text-xs">
							<thead class="bg-base-200/90 text-[10px] font-mono uppercase tracking-wider text-base-content/75 border-b border-base-300">
								<tr>
									<th class="w-10 text-center py-2">#</th>
									<th class="py-2 px-2.5">Vendor Contract Trap / Renewal Risk</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-base-200 text-[11px]">
								${vulns.map((v, i) => `
									<tr class="hover:bg-base-200/30">
										<td class="text-center font-mono text-error font-bold align-top py-2">${i + 1}</td>
										<td class="py-2 px-2.5 text-base-content/90 leading-relaxed break-words">${v}</td>
									</tr>
								`).join('')}
							</tbody>
						</table>
					</div>
				` : `
					<div class="p-6 text-center text-xs text-base-content/60 bg-base-100 rounded-xl border border-base-300">
						No pricing traps recorded.
					</div>
				`}
			</div>

			<!-- 4. BAKE-OFF LANDMINES TABLE -->
			<div id="comp-view-landmines" class="${compActiveTab === 'landmines' ? '' : 'hidden'} space-y-2 min-w-0">
				${traps.length > 0 ? `
					<div class="overflow-x-auto rounded-xl border border-base-300 bg-base-100 shadow-2xs">
						<table class="table table-xs md:table-sm w-full text-xs">
							<thead class="bg-base-200/90 text-[10px] font-mono uppercase tracking-wider text-base-content/75 border-b border-base-300">
								<tr>
									<th class="w-10 text-center py-2">#</th>
									<th class="py-2 px-2.5">Question to Corner ${compName}</th>
									<th class="w-16 text-right py-2 px-2.5">Copy</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-base-200 text-[11px]">
								${traps.map((q, i) => `
									<tr class="hover:bg-base-200/30">
										<td class="text-center font-mono text-primary font-bold align-top py-2">${i + 1}</td>
										<td class="py-2 px-2.5 italic text-base-content leading-relaxed break-words">"${q}"</td>
										<td class="text-right align-top py-2 px-2.5">
											<button type="button" class="btn btn-xs btn-ghost comp-copy-btn cursor-pointer" data-text="${encodeURIComponent(q)}">📋</button>
										</td>
									</tr>
								`).join('')}
							</tbody>
						</table>
					</div>
				` : `
					<div class="p-6 text-center text-xs text-base-content/60 bg-base-100 rounded-xl border border-base-300">
						No bake-off landmine questions recorded.
					</div>
				`}
			</div>

			<!-- 5. TACTICAL PLAYBOOK -->
			<div id="comp-view-playbook" class="${compActiveTab === 'playbook' ? '' : 'hidden'} space-y-2 min-w-0">
				${comp.displacement_playbook ? `
					<div class="card bg-base-100 border border-base-300 p-3.5 rounded-xl space-y-2 shadow-2xs">
						<div class="flex items-center justify-between border-b border-base-200 pb-1.5">
							<span class="text-xs font-bold text-base-content uppercase tracking-wider">🏆 Tactical Displacement Strategy</span>
							<span class="badge badge-xs badge-neutral">Playbook</span>
						</div>
						<p class="text-xs text-base-content/85 leading-relaxed whitespace-pre-line font-medium break-words">
							${comp.displacement_playbook}
						</p>
					</div>
				` : `
					<div class="p-6 text-center text-xs text-base-content/60 bg-base-100 rounded-xl border border-base-300">
						No displacement playbook generated.
					</div>
				`}
			</div>
		</div>
	`;

	// Subtab switching logic
	container.querySelectorAll('.comp-tab-btn').forEach((btn) => {
		btn.addEventListener('click', () => {
			const target = btn.getAttribute('data-tab') || 'matrix';
			compActiveTab = target;

			container.querySelectorAll('.comp-tab-btn').forEach((b) => {
				if (b.getAttribute('data-tab') === target) {
					b.className = 'btn btn-xs comp-tab-btn btn-neutral';
				} else {
					b.className = 'btn btn-xs comp-tab-btn btn-ghost';
				}
			});

			const vMatrix = document.getElementById('comp-view-matrix');
			const vMetrics = document.getElementById('comp-view-metrics');
			const vTraps = document.getElementById('comp-view-traps');
			const vLandmines = document.getElementById('comp-view-landmines');
			const vPlaybook = document.getElementById('comp-view-playbook');

			vMatrix?.classList.toggle('hidden', target !== 'matrix');
			vMetrics?.classList.toggle('hidden', target !== 'metrics');
			vTraps?.classList.toggle('hidden', target !== 'traps');
			vLandmines?.classList.toggle('hidden', target !== 'landmines');
			vPlaybook?.classList.toggle('hidden', target !== 'playbook');
		});
	});

	// Copy question handlers
	container.querySelectorAll('.comp-copy-btn').forEach((btn) => {
		btn.addEventListener('click', () => {
			const text = decodeURIComponent(btn.getAttribute('data-text') || '');
			if (text) {
				navigator.clipboard.writeText(text);
				const orig = btn.textContent;
				btn.textContent = '✓';
				setTimeout(() => { btn.textContent = orig; }, 2000);
			}
		});
	});

	// Refresh Crustdata button
	const btnRunCrust = document.getElementById('btn-run-crustdata-research');
	btnRunCrust?.addEventListener('click', async () => {
		if (onRefreshCrustdata) {
			btnRunCrust.setAttribute('disabled', 'true');
			const orig = btnRunCrust.innerHTML;
			btnRunCrust.innerHTML = '<span class="loading loading-spinner loading-xs"></span> Querying...';
			try {
				await onRefreshCrustdata();
			} finally {
				btnRunCrust.removeAttribute('disabled');
				btnRunCrust.innerHTML = orig;
			}
		}
	});
}
