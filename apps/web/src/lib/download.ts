import { API_URL, ApiError } from "@/lib/api";

export async function downloadFile(
  path: string,
  filename: string,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { credentials: "include" });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Network error");
  }
  if (!response.ok) {
    let data:
      | { code?: string; message?: string; details?: unknown }
      | undefined;
    try {
      data = await response.json();
    } catch {
      data = undefined;
    }
    throw new ApiError(
      response.status,
      data?.code ?? `HTTP_${response.status}`,
      data?.message ?? "Download failed",
      data?.details,
    );
  }
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
