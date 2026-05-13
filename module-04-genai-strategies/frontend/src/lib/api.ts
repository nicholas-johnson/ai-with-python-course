const API_BASE = '/api';

export type Message = {
	role: 'system' | 'user' | 'assistant';
	content: string;
};

export type ToolCall = {
	name: string;
	arguments: Record<string, unknown>;
};

export type ToolResult = {
	name: string;
	content: string;
};

export type ChatEvent =
	| { type: 'token'; token: string }
	| { type: 'tool_call'; data: ToolCall }
	| { type: 'tool_result'; data: ToolResult }
	| { type: 'done'; message: Message }
	| { type: 'error'; error: string };

export async function* streamChat(messages: Message[]): AsyncGenerator<ChatEvent> {
	const res = await fetch(`${API_BASE}/chat`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ messages }),
	});

	if (!res.ok) {
		yield { type: 'error', error: `HTTP ${res.status}: ${res.statusText}` };
		return;
	}

	const reader = res.body?.getReader();
	if (!reader) {
		yield { type: 'error', error: 'No response body' };
		return;
	}

	const decoder = new TextDecoder();
	let buffer = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		buffer += decoder.decode(value, { stream: true });
		const lines = buffer.split('\n');
		buffer = lines.pop() ?? '';

		let eventType = '';
		for (const line of lines) {
			if (line.startsWith('event: ')) {
				eventType = line.slice(7).trim();
			} else if (line.startsWith('data: ') && eventType) {
				try {
					const data = JSON.parse(line.slice(6));
					if (eventType === 'token') {
						yield { type: 'token', token: data.token };
					} else if (eventType === 'tool_call') {
						yield { type: 'tool_call', data };
					} else if (eventType === 'tool_result') {
						yield { type: 'tool_result', data };
					} else if (eventType === 'done') {
						yield { type: 'done', message: data };
					}
				} catch {
					// skip malformed JSON
				}
				eventType = '';
			} else if (line === '') {
				eventType = '';
			}
		}
	}
}

export async function getTools(): Promise<{ name: string; description: string }[]> {
	const res = await fetch(`${API_BASE}/tools`);
	if (!res.ok) return [];
	return res.json();
}

export type VisionResult = {
	description: string;
	key_points: string[];
};

export async function analyseImage(imageBase64: string, prompt: string): Promise<VisionResult> {
	const res = await fetch(`${API_BASE}/vision`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ image: imageBase64, prompt }),
	});
	if (!res.ok) throw new Error(`Vision failed: ${res.statusText}`);
	return res.json();
}

export async function transcribeAudio(file: File): Promise<{ transcript: string }> {
	const form = new FormData();
	form.append('file', file);
	const res = await fetch(`${API_BASE}/transcribe`, {
		method: 'POST',
		body: form,
	});
	if (!res.ok) throw new Error(`Transcription failed: ${res.statusText}`);
	return res.json();
}

export async function checkHealth(): Promise<boolean> {
	try {
		const res = await fetch(`${API_BASE}/health`);
		return res.ok;
	} catch {
		return false;
	}
}
