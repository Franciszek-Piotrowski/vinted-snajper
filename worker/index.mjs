const TIME_ZONE = "Europe/Warsaw";
const ACTIVE_START_MINUTE = 8 * 60;
const ACTIVE_END_MINUTE = 22 * 60;

export function isWithinActiveWindow(date) {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: TIME_ZONE,
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const hour = Number(parts.find((part) => part.type === "hour")?.value);
  const minute = Number(parts.find((part) => part.type === "minute")?.value);
  const localMinute = hour * 60 + minute;

  return (
    Number.isInteger(hour) &&
    Number.isInteger(minute) &&
    localMinute >= ACTIVE_START_MINUTE &&
    localMinute < ACTIVE_END_MINUTE
  );
}

export default {
  async fetch() {
    return new Response(
      "Vinted Sniper dispatcher is active. Cron runs every 5 minutes; GitHub dispatch is limited to 08:00-21:55 Europe/Warsaw.",
      {
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      },
    );
  },

  async scheduled(event, env) {
    const scheduledDate = new Date(event.scheduledTime);
    if (!isWithinActiveWindow(scheduledDate)) {
      console.log(
        `Outside ${TIME_ZONE} active window; skipped ${scheduledDate.toISOString()}.`,
      );
      return;
    }

    if (!env.GH_TOKEN) {
      throw new Error("Missing required Cloudflare secret GH_TOKEN.");
    }

    const repository = env.GITHUB_REPOSITORY;
    const workflow = env.GITHUB_WORKFLOW;
    const ref = env.GITHUB_REF;
    const response = await fetch(
      `https://api.github.com/repos/${repository}/actions/workflows/${workflow}/dispatches`,
      {
        method: "POST",
        headers: {
          Accept: "application/vnd.github+json",
          Authorization: `Bearer ${env.GH_TOKEN}`,
          "X-GitHub-Api-Version": "2022-11-28",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ref }),
      },
    );

    if (response.status !== 204) {
      const body = await response.text();
      throw new Error(
        `GitHub workflow dispatch failed (${response.status}): ${body}`,
      );
    }

    console.log(
      `Dispatched ${repository}/${workflow} for ${ref} at ${scheduledDate.toISOString()}.`,
    );
  },
};
