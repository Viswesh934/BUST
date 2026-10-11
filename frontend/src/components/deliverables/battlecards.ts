/**
 * Battlecards Stacked Flip Deck Deliverable View
 */

export function renderBattlecardsView(container: HTMLElement, art: any): void {
	const sideCards: any[] = art.content?.cards || [];
	if (!sideCards.length) {
		container.innerHTML = `
			<div class="p-6 text-center text-xs text-base-content/60 bg-base-100 rounded-xl border border-base-300">
				No battlecards formulated yet.
			</div>
		`;
		return;
	}

	let sideCardOrder: number[] = sideCards.map((_, i) => i);

	container.innerHTML = `
		<div class="space-y-3 min-w-0">
			<!-- Controls Bar -->
			<div class="flex items-center justify-between px-1">
				<div class="flex items-center gap-1.5 text-xs">
					<span class="badge badge-xs badge-neutral font-mono font-bold" id="side-deck-badge">
						Card 1 of ${sideCards.length}
					</span>
				</div>
				<div class="flex items-center gap-1">
					<button id="side-btn-flip" type="button" class="btn btn-xs btn-outline font-mono">
						Flip 🔄
					</button>
					<button id="side-btn-prev" type="button" class="btn btn-xs btn-outline px-2" title="Previous Card">
						❮
					</button>
					<button id="side-btn-next" type="button" class="btn btn-xs btn-neutral px-2" title="Next Card">
						❯
					</button>
				</div>
			</div>

			<!-- 3D Perspective Stack Stage -->
			<div class="relative w-full h-[370px] perspective-1000 my-2" id="side-deck-stage"></div>

			<!-- Progress Dots -->
			<div class="flex items-center justify-center gap-1.5 pt-1" id="side-deck-dots"></div>
		</div>
	`;

	const stage = document.getElementById('side-deck-stage');
	if (!stage) return;
	stage.innerHTML = '';

	sideCards.forEach((c, idx) => {
		const tags = c.tags || c.proof_points || ['Verified'];
		const item = document.createElement('div');
		item.className = 'side-card-item absolute inset-0 transition-all duration-500 cursor-pointer select-none';
		item.setAttribute('data-index', idx.toString());

		item.innerHTML = `
			<div class="flip-card h-full w-full">
				<div class="flip-card-inner h-full w-full relative">
					<!-- FRONT -->
					<div class="absolute inset-0 backface-hidden p-5 rounded-2xl border border-base-300 bg-base-100 flex flex-col justify-between shadow-xl">
						<div class="flex items-center justify-between border-b border-base-200 pb-2 gap-2">
							<span class="badge badge-xs badge-neutral font-bold uppercase tracking-wider truncate max-w-[140px] inline-block">${c.category || 'Objection'}</span>
							<span class="text-[10px] font-mono text-base-content/60 shrink-0">Click to Flip 🔄</span>
						</div>

						<div class="space-y-2 my-auto min-w-0">
							<span class="text-[10px] font-bold uppercase tracking-wider text-base-content/60">Prospect Objection:</span>
							<h4 class="text-sm font-bold text-base-content leading-snug break-words">
								"${c.objection_quote || c.objection}"
							</h4>
							<p class="text-[11px] text-base-content/75 truncate">
								Persona: ${c.buyer_persona || 'Executive Sponsor'}
							</p>
						</div>

						<div class="pt-2 border-t border-base-200 flex items-center justify-between text-[11px] gap-2">
							<div class="flex gap-1 max-w-[160px] overflow-hidden">
								${tags.slice(0, 1).map((t: string) => `<span class="badge badge-xs badge-outline truncate max-w-[130px] inline-block">${t}</span>`).join('')}
							</div>
							<span class="font-semibold text-primary shrink-0">Tap for talk-track →</span>
						</div>
					</div>

					<!-- BACK -->
					<div class="absolute inset-0 backface-hidden rotate-y-180 p-5 rounded-2xl border border-primary/40 bg-base-200 flex flex-col justify-between shadow-xl">
						<div class="flex items-center justify-between border-b border-base-300 pb-2 gap-2">
							<span class="badge badge-xs badge-success font-bold shrink-0">Winning Talk-Track</span>
							<span class="text-[10px] font-mono text-base-content/60 shrink-0">Flip Back ↺</span>
						</div>

						<div class="space-y-2 my-auto min-w-0">
							<div class="text-[11px] text-base-content leading-relaxed bg-base-100 p-3 rounded-xl border border-base-300 font-medium break-words max-h-[140px] overflow-y-auto">
								${c.winning_response || c.talk_track}
							</div>
							<div class="grid grid-cols-2 gap-1.5 text-[10px]">
								<div class="p-2 rounded-lg bg-base-100 border border-base-300 min-w-0">
									<span class="block text-base-content/60 uppercase font-mono">Proof:</span>
									<span class="font-semibold truncate block">${(c.proof_points || ['Validated metrics'])[0]}</span>
								</div>
								<div class="p-2 rounded-lg bg-base-100 border border-base-300 min-w-0">
									<span class="block text-base-content/60 uppercase font-mono">Metric:</span>
									<span class="font-semibold truncate block">${c.key_metric || '< 60-day break-even'}</span>
								</div>
							</div>
						</div>

						<div class="pt-2 border-t border-base-300 flex items-center justify-between text-[10px]">
							<span class="text-base-content/70">AE Confidence:</span>
							<div class="flex gap-1">
								<button class="btn btn-xs btn-outline py-0 h-5">Practice</button>
								<button class="btn btn-xs btn-neutral py-0 h-5">Mastered ✓</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		`;

		item.addEventListener('click', (e) => {
			const target = e.target as HTMLElement;
			if (target.tagName === 'BUTTON') return;
			if (sideCardOrder[0] === idx) {
				const flipCard = item.querySelector('.flip-card-inner');
				flipCard?.classList.toggle('is-flipped');
			}
		});

		stage.appendChild(item);
	});

	function updatePositions() {
		const items = Array.from(document.querySelectorAll('.side-card-item')) as HTMLElement[];
		items.forEach((card, originalIdx) => {
			const pos = sideCardOrder.indexOf(originalIdx);
			const flipCard = card.querySelector('.flip-card-inner');

			if (pos === 0) {
				card.style.zIndex = '30';
				card.style.transform = 'translateY(0) scale(1)';
				card.style.opacity = '1';
				card.style.pointerEvents = 'auto';
			} else if (pos === 1) {
				card.style.zIndex = '20';
				card.style.transform = 'translateY(14px) scale(0.96)';
				card.style.opacity = '0.85';
				card.style.pointerEvents = 'none';
				flipCard?.classList.remove('is-flipped');
			} else if (pos === 2) {
				card.style.zIndex = '10';
				card.style.transform = 'translateY(28px) scale(0.92)';
				card.style.opacity = '0.65';
				card.style.pointerEvents = 'none';
				flipCard?.classList.remove('is-flipped');
			} else {
				card.style.zIndex = '0';
				card.style.transform = 'translateY(42px) scale(0.88)';
				card.style.opacity = '0';
				card.style.pointerEvents = 'none';
				flipCard?.classList.remove('is-flipped');
			}
		});

		const badge = document.getElementById('side-deck-badge');
		if (badge && sideCards.length) {
			badge.textContent = `Card ${sideCardOrder[0] + 1} of ${sideCards.length}`;
		}

		const dotsContainer = document.getElementById('side-deck-dots');
		if (dotsContainer) {
			dotsContainer.innerHTML = '';
			sideCards.forEach((_, i) => {
				const dot = document.createElement('div');
				dot.className = `w-1.5 h-1.5 rounded-full transition-all ${sideCardOrder[0] === i ? 'bg-primary w-4' : 'bg-base-300'}`;
				dotsContainer.appendChild(dot);
			});
		}
	}

	const btnNext = document.getElementById('side-btn-next');
	const btnPrev = document.getElementById('side-btn-prev');
	const btnFlip = document.getElementById('side-btn-flip');

	btnNext?.addEventListener('click', () => {
		if (!sideCards.length) return;
		const items = Array.from(document.querySelectorAll('.side-card-item')) as HTMLElement[];
		const activeCard = items[sideCardOrder[0]];
		const flipCard = activeCard.querySelector('.flip-card-inner');
		flipCard?.classList.remove('is-flipped');

		activeCard.style.transform = 'translateX(110%) rotate(12deg) scale(0.9)';
		activeCard.style.opacity = '0';

		setTimeout(() => {
			const first = sideCardOrder.shift()!;
			sideCardOrder.push(first);
			updatePositions();
		}, 250);
	});

	btnPrev?.addEventListener('click', () => {
		if (!sideCards.length) return;
		const items = Array.from(document.querySelectorAll('.side-card-item')) as HTMLElement[];
		const lastIdx = sideCardOrder[sideCardOrder.length - 1];
		const lastCard = items[lastIdx];
		const flipCard = lastCard.querySelector('.flip-card-inner');
		flipCard?.classList.remove('is-flipped');

		lastCard.style.transform = 'translateX(-110%) rotate(-12deg) scale(0.9)';
		lastCard.style.opacity = '0';

		const last = sideCardOrder.pop()!;
		sideCardOrder.unshift(last);

		setTimeout(() => {
			updatePositions();
		}, 50);
	});

	btnFlip?.addEventListener('click', () => {
		if (!sideCards.length) return;
		const items = Array.from(document.querySelectorAll('.side-card-item')) as HTMLElement[];
		const activeCard = items[sideCardOrder[0]];
		const flipCard = activeCard.querySelector('.flip-card-inner');
		flipCard?.classList.toggle('is-flipped');
	});

	updatePositions();
}
