# Halal Momentum Web App

Static site served from GitHub Pages.

## Setup on GitHub

1. Push this repo to GitHub.
2. Go to **Settings → Pages**.
3. Under **Source**, select **Deploy from a branch**.
4. Pick the branch (e.g., `main`) and folder **`/docs`**.
5. Save. Your site will be at `https://<username>.github.io/<repo-name>/`.

## Daily updates

The GitHub Action in `.github/workflows/update-signal.yml` runs every weekday at 23:00 UTC (after US market close). It fetches the latest prices, recomputes the 9-1 month momentum signal, and commits an updated `data.json`.

You can also trigger it manually: **Actions → Update Momentum Signal → Run workflow**.

## Install to iPhone home screen

1. Open the GitHub Pages URL in **Safari** on iPhone.
2. Tap the **Share** button.
3. **Add to Home Screen** → name it "Halal Momentum".
4. It opens full-screen like a native app.
