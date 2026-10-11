import { marked } from 'marked';

// Configure marked for clean GFM and line breaks
marked.setOptions({
	gfm: true,
	breaks: true,
});

export function renderMarkdown(content: string): string {
	if (!content) return '';
	try {
		return marked.parse(content) as string;
	} catch (e) {
		console.error('Markdown parse error:', e);
		return content;
	}
}
