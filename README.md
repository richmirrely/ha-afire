# AFIRE Fireplace for Home Assistant

[![HACS validation](https://github.com/richmirrely/ha-afire/actions/workflows/validate.yml/badge.svg)](https://github.com/richmirrely/ha-afire/actions/workflows/validate.yml)

Local, cloud-free control of an AFIRE fireplace over the Gizwits GAgent LAN
protocol. Home Assistant connects directly to the fireplace on TCP port
`12416`; an AFIRE or Gizwits cloud account is not required.

## Entities

- Fireplace power (`switch`)
- Flame level 1–8 (`number`)
- Flame speed 1–8 (`number`)
- Orange decorative light (`light`)
- RGB light with 15 fixed colour presets and Smooth/Fade 1/Fade 2 effects (`light`)
- Exact fixed RGB colour preset (`select`)

The Home Assistant RGB colour picker is mapped to the nearest preset supported
by the fireplace. The separate preset selector exposes all 15 device colours
directly and always reports the preset currently active on the fireplace.

## Installation with HACS

1. Open **HACS → Integrations**.
2. Open the menu in the upper-right corner and choose **Custom repositories**.
3. Add `https://github.com/richmirrely/ha-afire` with category **Integration**.
4. Find **AFIRE Fireplace** in HACS and install it.
5. Restart Home Assistant when HACS asks you to do so.
6. Open **Settings → Devices & services → Add integration** and search for
   **AFIRE Fireplace**.
7. Enter the fireplace IP address and its 10-character local passcode.

Reserve the fireplace IP address in your router's DHCP settings. Home Assistant
and the fireplace must be able to communicate on the same local network.

## Manual installation

Copy `custom_components/afire` into `/config/custom_components/afire`, restart
Home Assistant, then add **AFIRE Fireplace** from **Settings → Devices &
services**.

## Protocol

The integration logs in with the local GAgent passcode and uses commands
`0x90/0x91` for state and `0x93/0x94` for control. All control remains inside
the local network.

## Supported hardware

This version targets the AFIRE product with Gizwits product key
`e2313fe07bca48fb82861d5f961993c5`.

## Об интеграции

Интеграция управляет камином напрямую по локальной сети, без облака. После
установки через HACS добавьте **AFIRE Fireplace** в разделе **Настройки →
Устройства и службы** и укажите IP-адрес камина и его 10-символьный локальный
passcode.

