/**
 * Buyer Deal Room Penthouse Suite Deliverable View
 */

export function renderSuiteView(container: HTMLElement, art: any, dealContext: any): void {
	const suite = art || {};
	const shareId = suite.share_id || 'suite_live';
	const accountName = dealContext.account_name || suite.account_name || 'Enterprise';

	container.innerHTML = `
		<div class="space-y-4 min-w-0 break-words">
			<div class="card bg-gradient-to-br from-base-200/80 to-base-300/80 border border-primary/40 p-5 rounded-2xl space-y-3 shadow-xs min-w-0">
				<div class="flex items-center justify-between gap-2">
					<span class="badge badge-xs badge-success font-semibold shrink-0">Active Keycard</span>
					<span class="font-mono text-[11px] text-base-content/70 truncate">${shareId}</span>
				</div>
				<h4 class="font-bold text-sm text-base-content break-words">Penthouse Suite: ${accountName}</h4>
				<p class="text-[11px] text-base-content/75 leading-relaxed break-words">
					Encrypted guest deal room for enterprise stakeholders to review objection talk-tracks, verified ROI metrics, and mutual milestones.
				</p>
				<a href="/suite?id=${shareId}" class="btn btn-sm btn-neutral w-full font-semibold shadow-xs">
					Open Guest Suite 🏨
				</a>
			</div>
		</div>
	`;
}
