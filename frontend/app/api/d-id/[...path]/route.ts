import { NextRequest, NextResponse } from "next/server";

const DID_API_KEY = "Z29vZ2xlLW9hdXRoMnwxMDk3OTI2MjMwMDE5NjU3MTU2MDhAYWtfM3k4YzJKRXFsWXhUeGY4T09feWp6:J-2Vrc7leP4o-IKvV0ZII";

async function proxyRequest(req: NextRequest, params: { path: string[] } | Promise<{ path: string[] }>) {
    try {
        const resolvedParams = await params;
        const path = resolvedParams.path ? resolvedParams.path.join('/') : '';
        const search = req.nextUrl.search;
        const url = `https://api.d-id.com/${path}${search}`;

        const headers: Record<string, string> = {
          "Authorization": `Basic ${Buffer.from(`${DID_API_KEY}:`).toString('base64')}`,
          "Content-Type": "application/json",
        };

        const init: RequestInit = {
          method: req.method,
          headers,
        };

        if (req.method !== "GET" && req.method !== "HEAD") {
          const bodyText = await req.text();
          if (bodyText) {
            init.body = bodyText;
          }
        }

        const response = await fetch(url, init);
        const contentType = response.headers.get('content-type')?.toLowerCase() ?? '';
        if (contentType.includes('application/json')) {
          const data = await response.json();
          return NextResponse.json(data, { status: response.status });
        } else {
          const arrayBuffer = await response.arrayBuffer();
          return new NextResponse(arrayBuffer, {
            status: response.status,
            headers: { "Content-Type": contentType },
          });
        }
    } catch (error: any) {
        console.error("D-ID proxy error:", error);
        return NextResponse.json({ error: error.message || "D-ID API proxy error" }, { status: 500 });
    }
}

export async function GET(req: NextRequest, context: { params: { path: string[] } }) {
    return proxyRequest(req, context.params);
}

export async function POST(req: NextRequest, context: { params: { path: string[] } }) {
    return proxyRequest(req, context.params);
}

export async function DELETE(req: NextRequest, context: { params: { path: string[] } }) {
    return proxyRequest(req, context.params);
}
