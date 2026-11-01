const API_BASE = '/api';

export type Message = {
	role: 'user' | 'assistant';
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

export type CalendarEvent = {
	id?: string;
	title: string;
	date: string;
	time?: string;
	location?: string;
	description?: string;
};

export type Reminder = {
	id?: string;
	title: string;
	due?: string;
	status?: string;
};

export async function* streamChat(
	message: string,
	history: Message[],
): AsyncGenerator<ChatEvent> {
	const messages = [...history, { role: 'user' as const, content: message }];
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

export async function getCalendar(): Promise<CalendarEvent[]> {
	const res = await fetch(`${API_BASE}/calendar`);
	if (!res.ok) throw new Error(`Failed to load calendar: ${res.statusText}`);
	return res.json();
}

export async function addCalendarEvent(event: CalendarEvent): Promise<CalendarEvent> {
	const res = await fetch(`${API_BASE}/calendar`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(event),
	});
	if (!res.ok) throw new Error(`Failed to add event: ${res.statusText}`);
	return res.json();
}

export async function getReminders(): Promise<Reminder[]> {
	const res = await fetch(`${API_BASE}/reminders`);
	if (!res.ok) throw new Error(`Failed to load reminders: ${res.statusText}`);
	return res.json();
}

export async function searchNotes(query: string): Promise<unknown> {
	const res = await fetch(`${API_BASE}/notes/search?q=${encodeURIComponent(query)}`);
	if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
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
