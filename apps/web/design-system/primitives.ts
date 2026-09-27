export type AxButtonTone = 'quiet' | 'standard';

export type AxEpistemicState =
  | 'observed'
  | 'potential'
  | 'unknown'
  | 'stale'
  | 'historical';

export interface AxButtonOptions {
  label: string;
  tone?: AxButtonTone;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}

export function createAxButton(options: AxButtonOptions): HTMLButtonElement {
  const button = document.createElement('button');
  button.className = 'ax-button';
  button.dataset.tone = options.tone ?? 'standard';
  button.type = options.type ?? 'button';
  button.disabled = options.disabled ?? false;
  button.textContent = options.label;
  return button;
}

export function setAxStatus(
  element: HTMLElement,
  state: AxEpistemicState,
  label: string,
): void {
  element.className = 'ax-status';
  element.dataset.state = state;
  element.textContent = label;
}
