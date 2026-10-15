/** Admin transport only: limits do not grant authority or manufacture data. */
export const ADMIN_RESPONSE_BYTE_LIMIT = 1_048_576;

export class AdminBodyLimitError extends Error {
  constructor() { super("Admin body byte limit exceeded"); }
}

/** Count actual bytes even when Content-Length is absent or dishonest. */
export async function readAdminText(body: ReadableStream<Uint8Array> | null, byteLimit: number): Promise<string> {
  if (!Number.isSafeInteger(byteLimit) || byteLimit < 1) throw new RangeError("Invalid Admin byte limit");
  if (!body) throw new SyntaxError("Missing Admin body");
  const reader = body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const part = await reader.read();
      if (part.done) break;
      size += part.value.byteLength;
      if (size > byteLimit) throw new AdminBodyLimitError();
      chunks.push(part.value);
    }
    try {
      return new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(Buffer.concat(chunks, size));
    } catch { throw new SyntaxError("Invalid Admin UTF-8"); }
  } catch (error) {
    // Cleanup must never replace the actual size/transport failure.
    try { void reader.cancel().catch(() => {}); } catch { /* preserve the original error */ }
    throw error;
  } finally { reader.releaseLock(); }
}

export async function readAdminRequestJson(request: Request, byteLimit: number): Promise<unknown> {
  return JSON.parse(await readAdminText(request.body, byteLimit));
}

/** Keep an upstream syntax/size failure out of the request-error (400/413) path. */
export async function readAdminResponseJson(response: Response): Promise<unknown> {
  try {
    return JSON.parse(await readAdminText(response.body, ADMIN_RESPONSE_BYTE_LIMIT));
  } catch { throw new Error("Invalid Admin upstream response"); }
}
