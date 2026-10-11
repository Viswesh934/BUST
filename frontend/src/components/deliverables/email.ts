/**
 * Proposal Email Deliverable View
 */

export function renderEmailView(container: HTMLElement, art: any): void {
	const email = art.content || {};

	container.innerHTML = `
		<div class="space-y-4 min-w-0 break-words">
			<div class="card bg-base-100 border border-base-300 p-4 rounded-xl space-y-3 shadow-2xs min-w-0">
				<div class="border-b border-base-200 pb-2 flex items-center justify-between gap-2">
					<div class="min-w-0">
						<span class="text-[10px] text-base-content/60 font-mono uppercase block truncate">Subject</span>
						<h4 class="font-bold text-xs text-base-content truncate">${email.subject || 'Proposal & Next Milestones'}</h4>
					</div>
					<button id="btn-copy-email" class="btn btn-xs btn-ghost gap-1 shrink-0 cursor-pointer" title="Copy to clipboard">
						📋 Copy
					</button>
				</div>
				<div class="text-[11px] text-base-content/85 whitespace-pre-line leading-relaxed bg-base-200/50 p-3.5 rounded-lg border border-base-300/60 break-words">
					${email.body || 'No email copy synthesized.'}
				</div>
				${email.key_takeaways?.length ? `
					<div class="flex flex-wrap gap-1 pt-1 max-w-full overflow-hidden">
						${email.key_takeaways.map((t: string) => `<span class="badge badge-xs badge-neutral truncate max-w-[130px] inline-block">${t}</span>`).join('')}
					</div>
				` : ''}
			</div>
		</div>
	`;

	const copyBtn = document.getElementById('btn-copy-email');
	copyBtn?.addEventListener('click', () => {
		navigator.clipboard.writeText(`${email.subject || ''}\n\n${email.body || ''}`);
		copyBtn.textContent = 'Copied ✓';
		setTimeout(() => { copyBtn.textContent = '📋 Copy'; }, 2000);
	});
}
