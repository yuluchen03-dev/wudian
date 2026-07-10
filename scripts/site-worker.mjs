const htmlRequest = (request) =>
  request.headers.get("accept")?.toLowerCase().includes("text/html");

const assetRequest = (request, pathname) => {
  const url = new URL(request.url);
  url.pathname = pathname;
  return new Request(url, request);
};

const candidatePaths = (pathname) => {
  const normalized = pathname.replace(/\/+$/, "") || "/";
  if (normalized === "/") return ["/index.html"];
  return [`${normalized}.html`, `${normalized}/index.html`];
};

const worker = {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    if (response.status !== 404 || !htmlRequest(request)) return response;

    for (const pathname of candidatePaths(new URL(request.url).pathname)) {
      const fallback = await env.ASSETS.fetch(assetRequest(request, pathname));
      if (fallback.status !== 404) return fallback;
    }

    return response;
  },
};

export default worker;
