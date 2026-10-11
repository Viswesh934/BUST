/**
 * Mutual Action Plan (MAP) Flowchart Deliverable View
 */

export function renderFlowchartView(container: HTMLElement, art: any): void {
	const map = art.content || {};
	const stages: any[] = map.stages || [];

	if (!stages.length) {
		container.innerHTML = `
			<div class="p-6 text-center text-xs text-base-content/60 bg-base-100 rounded-xl border border-base-300">
				No mutual action plan milestones defined yet.
			</div>
		`;
		return;
	}

	container.innerHTML = `
		<div class="space-y-4 min-w-0 break-words">
			<div class="space-y-2.5 min-w-0">
				${stages.map((st: any) => `
					<div class="card bg-base-100 border border-base-300 p-3.5 rounded-xl space-y-1.5 shadow-2xs min-w-0 break-words">
						<div class="flex items-center justify-between gap-2">
							<span class="badge badge-xs ${st.status === 'completed' ? 'badge-success' : 'badge-neutral'} font-semibold shrink-0">Stage ${st.stage_number}</span>
							<span class="text-[10px] font-mono text-base-content/60 truncate max-w-[120px]">${st.target_date || ''}</span>
						</div>
						<h4 class="font-bold text-xs text-base-content break-words">${st.name}</h4>
						<p class="text-[11px] text-base-content/75 leading-relaxed break-words">${st.description || ''}</p>
						<div class="text-[10px] text-base-content/60 font-mono pt-1 flex justify-between gap-2 border-t border-base-200">
							<span class="truncate">Owner: ${st.owner || 'AE'}</span>
							<span class="truncate">Deliverable: ${st.deliverable || 'Approved'}</span>
						</div>
					</div>
				`).join('')}
			</div>
		</div>
	`;
}
