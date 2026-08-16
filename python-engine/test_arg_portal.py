"""Standalone Launcher to test the ARG Localhost Portal & Desktop Puzzles.

Run with:
    python test_arg_portal.py
"""

import asyncio
import sys
from src.core.event_bus import EventBus
from src.story.arg_server import ARGServer
from src.story.puzzles.desktop_arg import DesktopARGPuzzle


async def main():
    print("=================================================================")
    print("      SENTIENT_OS v2 — ARG CONTAINMENT PORTAL TEST LAUNCHER      ")
    print("=================================================================")

    event_bus = EventBus()
    desktop_puzzle = DesktopARGPuzzle()
    arg_server = ARGServer(event_bus=event_bus, port=6660)

    # 1. Deploy desktop secret files
    print("\n[1/3] Masaüstüne şifreli araştırma dosyaları bırakılıyor...")
    created = desktop_puzzle.deploy_puzzle_files()
    for f in created:
        print(f"  → Oluşturuldu: {f}")

    # 2. Start ARG HTTP Server
    print(f"\n[2/3] Localhost ARG Web Sunucusu başlatılıyor ({arg_server.url})...")
    await arg_server.start()

    # 3. Open Web Browser
    print(f"[3/3] Tarayıcı açılıyor: {arg_server.url}")
    arg_server.launch_browser()

    print("\n" + "=" * 65)
    print(">>> PORTAL AKTİF! Tarayıcınızda açılan sayfayı inceleyin.")
    print(">>> Masaüstündeki 'SENTIENT_INCIDENT_REPORT_89.txt' dosyasını okuyun.")
    print(">>> Frekans modülünü 440 Hz'e ayarlayıp şifreyi terminale girin.")
    print(">>> Kapatmak için terminalde Ctrl + C tuşlayın.")
    print("=" * 65 + "\n")

    solved_event = asyncio.Event()

    async def on_solved(event_type: str, **kwargs):
        print(f"\n[✓ TEBRİKLER] ARG Bulmacası Başarıyla Çözüldü! Detaylar: {kwargs}")
        solved_event.set()

    await event_bus.subscribe("puzzle.arg_solved", on_solved)

    try:
        # Wait until solved or user terminates
        await solved_event.wait()
        print("\nSistem 5 saniye içinde temizleniyor...")
        await asyncio.sleep(5)
    except KeyboardInterrupt:
        print("\nKullanıcı tarafından durduruldu.")
    finally:
        print("\nTemizlik yapılıyor...")
        desktop_puzzle.cleanup()
        await arg_server.stop()
        print("✓ Masaüstü dosyaları silindi ve sunucu kapatıldı.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
