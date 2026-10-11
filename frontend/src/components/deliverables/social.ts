/**
 * Executive Social Touchpoint & Stakeholder Network Graph View
 */

export function renderSocialView(container: HTMLElement, art: any, dealContext: any): void {
	const soc = art.content || {};
	const stakeholders = soc.stakeholders || [
		{
			id: 'sponsor',
			name: soc.recipient || 'Executive Sponsor',
			role: 'Executive Sponsor',
			channel: 'X / Twitter DM',
			handle: `@${(dealContext.account_name || 'account').toLowerCase()}_lead`,
			avatar_icon: '⚡',
			dm: soc.executive_dm || '',
			hook: soc.public_hook || '',
			influence_level: 'Executive Sponsor'
		},
		{
			id: 'cfo',
			name: 'Chief Financial Officer',
			role: 'Economic Buyer',
			channel: 'LinkedIn InMail',
			handle: 'in/cfo-board',
			avatar_icon: '💼',
			dm: `Re: ${dealContext.account_name || 'Enterprise'} ROI modeling. Our commercial analysis indicates sub-210-day break-even and validated annual savings. Happy to send over our executive 1-page financial impact brief.`,
			hook: 'Capital efficiency in enterprise SaaS is no longer optional. How modern infrastructure leaders evaluate vendor payback periods.',
			influence_level: 'Decision Authority'
		},
		{
			id: 'tech_lead',
			name: 'Principal Infrastructure Architect',
			role: 'Technical Champion',
			channel: 'Public X / Thread',
			handle: `@${(dealContext.account_name || 'account').toLowerCase()}_eng`,
			avatar_icon: '🛠️',
			dm: `Saw your work on ${dealContext.account_name || 'the stack'}. We eliminated migration cutover downtime with zero data loss. Would love to compare technical benchmarks.`,
			hook: 'Migration downtime is an architectural choice, not an inevitability. How decoupled workflows cut cutover risk by 80%.',
			influence_level: 'Key Evaluator'
		}
	];

	let activeIdx = 0;

	function renderInner() {
		const cur = stakeholders[activeIdx] || stakeholders[0];
		const accountName = dealContext.account_name || soc.account_name || 'Enterprise';

		container.innerHTML = `
			<div class="space-y-4 select-none min-w-0 break-words">
				<!-- INTERACTIVE SOCIAL GRAPH CANVAS -->
				<div class="card bg-base-100 border border-base-300 p-3 rounded-2xl shadow-xs space-y-3 min-w-0">
					<div class="flex items-center justify-between border-b border-base-200 pb-2 gap-2">
						<div class="flex items-center gap-1.5 min-w-0">
							<span class="text-xs font-bold text-base-content uppercase tracking-wider truncate">Stakeholder Social Graph</span>
							<span class="badge badge-xs badge-success font-mono font-bold shrink-0">Network Map</span>
						</div>
						<span class="text-[10px] text-base-content/60 font-mono shrink-0">Tap node</span>
					</div>

					<div class="relative w-full h-[180px] bg-base-200/50 rounded-xl border border-base-300/60 overflow-hidden flex items-center justify-center">
						<svg class="absolute inset-0 w-full h-full pointer-events-none z-0">
							<line x1="50%" y1="50%" x2="20%" y2="28%" stroke="currentColor" class="text-base-content/25" stroke-width="2" stroke-dasharray="4" />
							<line x1="50%" y1="50%" x2="80%" y2="28%" stroke="currentColor" class="text-base-content/25" stroke-width="2" stroke-dasharray="4" />
							<line x1="50%" y1="50%" x2="50%" y2="80%" stroke="currentColor" class="text-base-content/25" stroke-width="2" stroke-dasharray="4" />
							<line x1="20%" y1="28%" x2="80%" y2="28%" stroke="currentColor" class="text-primary/30" stroke-width="1.5" />
						</svg>

						<!-- Central Account Node -->
						<div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10 text-center">
							<div class="w-12 h-12 rounded-2xl bg-neutral text-neutral-content flex items-center justify-center text-lg font-bold shadow-lg border-2 border-base-100">
								🏢
							</div>
							<span class="block mt-1 text-[10px] font-bold text-base-content font-mono truncate max-w-[90px]">
								${accountName}
							</span>
						</div>

						<!-- Stakeholder Node 1 (Sponsor) -->
						<div class="social-node-btn absolute left-[12%] top-[16%] z-20 cursor-pointer flex flex-col items-center transition-all ${activeIdx === 0 ? 'scale-110' : 'hover:scale-105 opacity-80'}" data-index="0">
							<div class="w-10 h-10 rounded-full bg-base-100 border-2 ${activeIdx === 0 ? 'border-primary ring-2 ring-primary/40 bg-primary/10 shadow-md' : 'border-base-300 shadow-xs'} flex items-center justify-center text-sm">
								${stakeholders[0]?.avatar_icon || '⚡'}
							</div>
							<span class="mt-1 text-[9px] font-bold text-base-content bg-base-100/90 px-1 rounded truncate max-w-[80px]">
								${stakeholders[0]?.name?.split(' ')[0] || 'Sponsor'}
							</span>
						</div>

						<!-- Stakeholder Node 2 (CFO) -->
						<div class="social-node-btn absolute right-[12%] top-[16%] z-20 cursor-pointer flex flex-col items-center transition-all ${activeIdx === 1 ? 'scale-110' : 'hover:scale-105 opacity-80'}" data-index="1">
							<div class="w-10 h-10 rounded-full bg-base-100 border-2 ${activeIdx === 1 ? 'border-primary ring-2 ring-primary/40 bg-primary/10 shadow-md' : 'border-base-300 shadow-xs'} flex items-center justify-center text-sm">
								${stakeholders[1]?.avatar_icon || '💼'}
							</div>
							<span class="mt-1 text-[9px] font-bold text-base-content bg-base-100/90 px-1 rounded truncate max-w-[80px]">
								${stakeholders[1]?.name?.split(' ')[0] || 'CFO'}
							</span>
						</div>

						<!-- Stakeholder Node 3 (Tech Lead) -->
						<div class="social-node-btn absolute left-1/2 bottom-[8%] -translate-x-1/2 z-20 cursor-pointer flex flex-col items-center transition-all ${activeIdx === 2 ? 'scale-110' : 'hover:scale-105 opacity-80'}" data-index="2">
							<div class="w-10 h-10 rounded-full bg-base-100 border-2 ${activeIdx === 2 ? 'border-primary ring-2 ring-primary/40 bg-primary/10 shadow-md' : 'border-base-300 shadow-xs'} flex items-center justify-center text-sm">
								${stakeholders[2]?.avatar_icon || '🛠️'}
							</div>
							<span class="mt-1 text-[9px] font-bold text-base-content bg-base-100/90 px-1 rounded truncate max-w-[80px]">
								${stakeholders[2]?.name?.split(' ')[0] || 'Tech'}
							</span>
						</div>
					</div>
				</div>

				<!-- SELECTED STAKEHOLDER TOUCHPOINT DOSSIER -->
				<div class="space-y-3 min-w-0">
					<div class="flex items-center justify-between p-3 rounded-xl bg-base-200/70 border border-base-300 gap-2">
						<div class="flex items-center gap-2.5 min-w-0">
							<div class="w-9 h-9 rounded-full bg-base-100 border border-base-300 flex items-center justify-center text-base shadow-xs shrink-0">
								${cur.avatar_icon || '👤'}
							</div>
							<div class="min-w-0">
								<h4 class="text-xs font-bold text-base-content truncate">${cur.name}</h4>
								<p class="text-[10px] text-base-content/70 font-mono truncate max-w-[180px]">${cur.role} • ${cur.handle || ''}</p>
							</div>
						</div>
						<div class="flex flex-col items-end gap-1 shrink-0">
							<span class="badge badge-xs badge-neutral font-semibold truncate max-w-[100px] inline-block">${cur.channel || 'Direct'}</span>
							<span class="badge badge-xs badge-outline text-[9px] truncate max-w-[100px] inline-block">${cur.influence_level || 'Stakeholder'}</span>
						</div>
					</div>

					<!-- Direct Message (DM) -->
					<div class="card bg-base-100 border border-base-300 p-3.5 rounded-xl space-y-2 shadow-2xs min-w-0">
						<div class="flex items-center justify-between border-b border-base-200 pb-1.5 gap-2">
							<span class="text-[10px] font-bold text-base-content uppercase tracking-wider truncate">Targeted Direct Message (DM)</span>
							<button type="button" class="btn btn-xs btn-ghost copy-text-btn cursor-pointer shrink-0" data-target="soc-target-dm">📋 Copy DM</button>
						</div>
						<div id="soc-target-dm" class="text-xs text-base-content/90 leading-relaxed bg-base-200/50 p-2.5 rounded-lg border border-base-300/60 font-medium whitespace-pre-line break-words">
							${cur.dm || cur.touchpoint || soc.executive_dm || ''}
						</div>
					</div>

					<!-- Public Engagement Hook -->
					<div class="card bg-base-100 border border-base-300 p-3.5 rounded-xl space-y-2 shadow-2xs min-w-0">
						<div class="flex items-center justify-between border-b border-base-200 pb-1.5 gap-2">
							<span class="text-[10px] font-bold text-base-content uppercase tracking-wider truncate">Public Engagement Hook</span>
							<button type="button" class="btn btn-xs btn-ghost copy-text-btn cursor-pointer shrink-0" data-target="soc-target-hook">📋 Copy Hook</button>
						</div>
						<div id="soc-target-hook" class="text-xs text-base-content/90 leading-relaxed bg-base-200/50 p-2.5 rounded-lg border border-base-300/60 whitespace-pre-line break-words">
							${cur.hook || soc.public_hook || ''}
						</div>
					</div>

					${soc.provocative_question ? `
						<div class="card bg-base-100 border border-base-300 p-3 rounded-xl space-y-1.5 shadow-2xs min-w-0">
							<div class="flex items-center justify-between border-b border-base-200 pb-1 gap-2">
								<span class="text-[10px] font-bold text-base-content uppercase tracking-wider truncate">Discovery Question</span>
								<button type="button" class="btn btn-xs btn-ghost copy-text-btn cursor-pointer shrink-0" data-target="soc-target-q">📋 Copy</button>
							</div>
							<div id="soc-target-q" class="text-[11px] text-base-content/90 leading-relaxed bg-base-200/50 p-2 rounded-lg border border-base-300/60 italic break-words">
								"${soc.provocative_question}"
							</div>
						</div>
					` : ''}
				</div>
			</div>
		`;

		container.querySelectorAll('.social-node-btn').forEach((btn) => {
			btn.addEventListener('click', () => {
				const idx = parseInt(btn.getAttribute('data-index') || '0', 10);
				activeIdx = idx;
				renderInner();
			});
		});

		container.querySelectorAll('.copy-text-btn').forEach((btn) => {
			btn.addEventListener('click', () => {
				const targetId = btn.getAttribute('data-target');
				const el = document.getElementById(targetId || '');
				if (el) {
					navigator.clipboard.writeText(el.textContent?.trim() || '');
					const orig = btn.textContent;
					btn.textContent = 'Copied ✓';
					setTimeout(() => { btn.textContent = orig; }, 2000);
				}
			});
		});
	}

	renderInner();
}
