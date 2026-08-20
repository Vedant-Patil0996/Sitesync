import { NextRequest, NextResponse } from "next/server";

const DID_API_KEY_BASE64 = "WjI5dloyeGxMVzloZFhSb01ud3hNRGszT1RJMk1qTXdNREU1TmpVM01UVTJNRGhBWVd0Zk0zazRZekpLUlhGc1dYaFVlR1k0VDA5ZmVXcDY6Si0yVnJjN2xlUDRvLUlLdlYwWklJ";

export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
    try {
        const path = params.path.join('/');
        const url = `https://api.d-id.com/${path}`;
        const body = await req.json();

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Authorization": `Basic ${DID_API_KEY_BASE64}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}

export async function DELETE(req: NextRequest, { params }: { params: { path: string[] } }) {
    try {
        const path = params.path.join('/');
        const url = `https://api.d-id.com/${path}`;

        const response = await fetch(url, {
            method: "DELETE",
            headers: {
                "Authorization": `Basic ${DID_API_KEY_BASE64}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();
        return NextResponse.json(data, { status: response.status });
    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
