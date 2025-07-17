async function main() {
  // Keep process alive until Ctrl+C
  process.stdin.resume();

  process.on("SIGINT", () => {
    console.log("\n[MAIN] Shutting down...");
    console.log("[MAIN] ✅ Clean shutdown complete");
    process.exit(0);
  });
}

if (import.meta.url === new URL(process.argv[1], import.meta.url).href) {
  main();
}
