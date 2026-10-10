// export const API_URL = (
//   process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
// ).replace(/\/+$/, "");

// export class ApiError extends Error {
//   status: number;
//   code: string;

//   constructor(status: number, code: string, message: string) {
//     super(message);
//     this.status = status;
//     this.code = code;
//   }

//   get userMessage(): string {
//     if (this.status === 0)
//       return "We can't reach the server. Is the API running?";
//     if (this.status >= 500)
//       return "Something went wrong on the server. Please try again.";
//     return this.message;
//   }
// }

// async function request<T>(path: string, init?: RequestInit): Promise<T> {
//   let response: Response;
//   try {
//     response = await fetch(`${API_URL}${path}`, {
//       ...init,
//       headers: {
//         Accept: "application/json",
//         ...(init?.body ? { "Content-Type": "application/json" } : {}),
//       },
//     });
//   } catch {
//     throw new ApiError(0, "NETWORK_ERROR", "Network error");
//   }

//   const text = await response.text();
//   let data: any;
//   try {
//     data = text ? JSON.parse(text) : undefined;
//   } catch {
//     data = undefined;
//   }

//   if (!response.ok) {
//     throw new ApiError(
//       response.status,
//       data?.code ?? `HTTP_${response.status}`,
//       data?.message ?? "Request failed",
//     );
//   }
//   return data as T;
// }

// export const api = {
//   get: <T>(path: string) => request<T>(path),
//   post: <T>(path: string, body?: unknown) =>
//     request<T>(path, { method: "POST", body: JSON.stringify(body) }),
// };

export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"
).replace(/\/+$/, "");

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(
    status: number,
    code: string,
    message: string,
    details?: unknown,
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }

  get userMessage(): string {
    if (this.status === 0)
      return "We can't reach the server. Is the API running?";
    if (this.status >= 500)
      return "Something went wrong on the server. Please try again.";
    return this.message;
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      credentials: "include", // sends the login cookie
      headers: {
        Accept: "application/json",
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Network error");
  }

  const text = await response.text();
  let data: { code?: string; message?: string; details?: unknown } | undefined;
  try {
    data = text ? JSON.parse(text) : undefined;
  } catch {
    data = undefined;
  }

  if (!response.ok) {
    throw new ApiError(
      response.status,
      data?.code ?? `HTTP_${response.status}`,
      data?.message ?? "Request failed",
      data?.details,
    );
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) =>
    request<T>("POST", path, body ?? {}),
  patch: <T>(path: string, body?: unknown) =>
    request<T>("PATCH", path, body ?? {}),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body ?? {}),
  delete: <T>(path: string) => request<T>("DELETE", path),
};
