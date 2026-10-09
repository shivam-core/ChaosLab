export async function request(path, options = {}) {
  const token = sessionStorage.getItem("chaoslab_token");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const headers = { "Content-Type": "application/json" };
    if (token) headers["X-Lab-Token"] = token;
    const response = await fetch(path, {
      ...options,
      headers: { ...headers, ...(options.headers || {}) },
      signal: controller.signal,
      cache: "no-store",
    });
    const body = await response.json();
    if (!response.ok) {
      const error = new Error(body.message || "Request failed");
      error.status = response.status;
      error.code = body.code;
      throw error;
    }
    return body;
  } finally {
    clearTimeout(timeout);
  }
}
