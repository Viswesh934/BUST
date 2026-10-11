/**
 * Pitch Presentation Deck Deliverable View
 */

export function renderPresentationView(container: HTMLElement, art: any): void {
	const slides: any[] = art.content?.slides || [];
	if (!slides.length) {
		container.innerHTML = `
			<div class="p-6 text-center text-xs text-base-content/60 bg-base-100 rounded-xl border border-base-300">
				No presentation slides generated yet.
			</div>
		`;
		return;
	}

	container.innerHTML = `
		<div class="space-y-3 min-w-0 break-words">
			<!-- Presentation Header Banner -->
			<div class="card bg-base-100 border border-base-300 p-3.5 rounded-xl shadow-2xs flex items-center justify-between gap-2 min-w-0">
				<div class="space-y-0.5 min-w-0">
					<span class="text-[10px] font-bold uppercase tracking-wider text-base-content/60">Executive Pitch Deck</span>
					<div class="text-xs font-bold text-base-content flex items-center gap-1.5 flex-wrap">
						<span>📊 16:9 Widescreen Studio</span>
						<span class="badge badge-xs badge-neutral font-mono font-bold">${slides.length} Slides Total</span>
					</div>
				</div>
				<a href="/presentations" class="btn btn-xs btn-neutral gap-1 font-semibold shrink-0">
					<span>Launch Studio 🖥️</span>
				</a>
			</div>

			<!-- Slide Cards List -->
			<div class="space-y-2.5 min-w-0">
				${slides.map((s: any, idx: number) => `
					<div class="card bg-base-100 border border-base-300 p-4 rounded-xl space-y-2.5 shadow-2xs min-w-0 break-words overflow-hidden">
						<div class="flex items-center justify-between border-b border-base-200/80 pb-2 gap-2">
							<span class="badge badge-xs badge-neutral font-semibold truncate max-w-[140px] inline-block">${s.tag || `Slide ${idx + 1}`}</span>
							<span class="badge badge-xs badge-outline font-mono font-bold shrink-0">Slide ${idx + 1} of ${slides.length}</span>
						</div>
						<h4 class="font-bold text-xs text-base-content break-words">${s.title}</h4>
						${s.subtitle ? `<p class="text-[11px] text-base-content/75 break-words">${s.subtitle}</p>` : ''}
						<ul class="text-[11px] space-y-1.5 pt-1 text-base-content/85">
							${(s.bullets || []).map((b: string) => `
								<li class="flex items-start gap-1.5 leading-relaxed min-w-0">
									<span class="text-primary font-bold shrink-0 mt-0.5">✓</span>
									<span class="break-words">${b}</span>
								</li>
							`).join('')}
						</ul>
						${s.speaker_note ? `
							<div class="mt-2 p-2.5 bg-base-200/60 rounded-lg text-[10px] text-base-content/75 italic border border-base-300/60 break-words">
								<span class="font-semibold not-italic">Speaker Note:</span> ${s.speaker_note}
							</div>
						` : ''}
					</div>
				`).join('')}
			</div>
		</div>
	`;
}
