#!/usr/bin/env bash
# Generate one narration clip using an Azure AI Foundry MAI-Voice-2 /
# MAI-Voice-2-Flash voice via an existing Azure AI Services (Speech)
# resource, authenticating with Microsoft Entra ID (works even when the
# resource has disableLocalAuth=true, so no subscription key is needed).
#
# Usage:
#   tts_azure_mai_voice.sh <text> <out.wav> [voice] [resource-name] [resource-group]
#
# voice/resource-name/resource-group fall back to the AZURE_SPEECH_VOICE /
# AZURE_SPEECH_RESOURCE_NAME / AZURE_SPEECH_RESOURCE_GROUP env vars if
# omitted. Requires `az login` with at least "Cognitive Services User" on
# the target resource.
#
# Voice name format: "<locale>-<Name>:MAI-Voice-2" or ":MAI-Voice-2-Flash"
# (e.g. en-US-Harper:MAI-Voice-2). List everything a resource actually
# offers with:
#   curl -s -H "Authorization: Bearer aad#<resourceId>#<entraToken>" \
#     "https://<resource>.cognitiveservices.azure.com/tts/cognitiveservices/voices/list" \
#     | grep -o '"ShortName": *"[^"]*MAI-Voice[^"]*"'
set -euo pipefail

TEXT="${1:?narration text}"
OUT="${2:?output .wav path}"
VOICE="${3:-${AZURE_SPEECH_VOICE:-en-US-Harper:MAI-Voice-2}}"
RESOURCE_NAME="${4:-${AZURE_SPEECH_RESOURCE_NAME:?set AZURE_SPEECH_RESOURCE_NAME or pass as 4th arg}}"
RESOURCE_GROUP="${5:-${AZURE_SPEECH_RESOURCE_GROUP:?set AZURE_SPEECH_RESOURCE_GROUP or pass as 5th arg}}"

RESOURCE_ID=$(az cognitiveservices account show -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query id -o tsv)
ENDPOINT=$(az cognitiveservices account show -n "$RESOURCE_NAME" -g "$RESOURCE_GROUP" --query properties.endpoint -o tsv)
ENDPOINT="${ENDPOINT%/}"
TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com --query accessToken -o tsv)
AUTH="aad#${RESOURCE_ID}#${TOKEN}"

ESCAPED=$(python3 -c "import sys, html; print(html.escape(sys.argv[1]))" "$TEXT")
SSML="<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'><voice xml:lang='en-US' name='${VOICE}'>${ESCAPED}</voice></speak>"

synthesize() {
  curl -s -X POST "${ENDPOINT}/tts/cognitiveservices/v1" \
    -H "Authorization: Bearer ${AUTH}" \
    -H "Content-Type: application/ssml+xml" \
    -H "X-Microsoft-OutputFormat: riff-24khz-16bit-mono-pcm" \
    -H "User-Agent: narrative-walkthrough" \
    --data-binary "$SSML" \
    -o "$OUT" -w "%{http_code}"
}

# NOTE: the working synthesis path is "/tts/cognitiveservices/v1" -- NOT
# the bare "/cognitiveservices/v1" shown in key-based docs examples; the
# "/tts/" prefix is required for Entra-token auth against a multi-service
# AIServices account. A resource that's been idle can also occasionally
# 502 on the very first call after a while; one retry clears it.
STATUS=$(synthesize)
if [ "$STATUS" != "200" ]; then
  sleep 3
  STATUS=$(synthesize)
fi

if [ "$STATUS" != "200" ]; then
  echo "TTS request failed (HTTP $STATUS): $(cat "$OUT")" >&2
  exit 1
fi

echo "Wrote $OUT"
