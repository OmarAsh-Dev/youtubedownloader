export default function handler(req, res) {
  const url = req.query.url;
  if (!url) {
    return res.status(400).json({ error: "No URL provided" });
  }

  try {
    const match = url.match(/(?:v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
    if (!match) {
      return res.status(400).json({ error: "Invalid URL" });
    }
    const video_id = match[1];
    return res.json({ video_id });
  } catch (err) {
    return res.status(500).json({ error: "Server error: " + err.message });
  }
}
