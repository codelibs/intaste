// Copyright (c) 2025 CodeLibs
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//     http://www.apache.org/licenses/LICENSE-2.0
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * Streaming proxy for /api/v1/assist/query endpoint
 * Proxies SSE streaming responses from intaste-api to the client
 */

import { NextRequest } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  const apiProxyUrl = process.env.API_PROXY_URL;

  if (!apiProxyUrl) {
    return new Response(
      JSON.stringify({ code: 'CONFIG_ERROR', message: 'API_PROXY_URL not configured' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    // Parse request body
    const body = await request.json();

    // Forward headers
    const headers = new Headers();
    headers.set('Content-Type', 'application/json');
    headers.set('Accept', 'text/event-stream');

    // Forward X-Intaste-Token if present
    const token = request.headers.get('X-Intaste-Token');
    if (token) {
      headers.set('X-Intaste-Token', token);
    }

    // Forward X-Request-ID if present
    const requestId = request.headers.get('X-Request-ID');
    if (requestId) {
      headers.set('X-Request-ID', requestId);
    }

    // Make streaming request to backend API
    const apiUrl = `${apiProxyUrl}/api/v1/assist/query`;
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return new Response(errorText, {
        status: response.status,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    if (!response.body) {
      return new Response(
        JSON.stringify({ code: 'PROXY_ERROR', message: 'No response body from API' }),
        { status: 500, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Create streaming response with SSE headers
    return new Response(response.body, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        Connection: 'keep-alive',
        'X-Accel-Buffering': 'no', // Disable nginx buffering
      },
    });
  } catch (error) {
    console.error('Streaming proxy error:', error);
    return new Response(
      JSON.stringify({
        code: 'PROXY_ERROR',
        message: error instanceof Error ? error.message : 'Unknown error',
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
