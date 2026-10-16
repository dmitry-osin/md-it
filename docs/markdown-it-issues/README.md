# Markdown-It — Bug Reports and Feature Requests

This repository is the issue tracker for **Markdown-It**, a Chrome extension that converts web page content to Markdown locally in your browser. Use it to report bugs, suggest improvements, and ask questions about the extension.

- **Website and installation:** [dmitry-osin.github.io/md-it](https://dmitry-osin.github.io/md-it/?lang=en)
- **Report a bug or suggest a feature:** [GitHub Issues](https://github.com/dmitry-osin/markdown-it-issues/issues)
- **Privacy policy:** [dmitry-osin.github.io/md-it/policy](https://dmitry-osin.github.io/md-it/policy?lang=en)
- **Publisher:** [Dmitry Osin](https://github.com/dmitry-osin)

## What is Markdown-It?

Markdown-It helps you save web content as Markdown for your notes, documentation, and knowledge base.

Choose what to convert:

- The entire current page.
- Selected text.
- A specific element using the Element Picker.
- An article area saved as a Content Root in a site profile.

Copy the result, download a `.md` file, or open **Preview** to inspect the Markdown source, its rendered view, and conversion diagnostics.

The extension supports site profiles, cleanup rules, conversion preferences, and configuration import and export. Its interface is available in English and Russian.

## Installation

Visit the [official Markdown-It website](https://dmitry-osin.github.io/md-it/?lang=en) for getting-started instructions and the Chrome Web Store installation link. The link appears once the listing's availability is confirmed. While the listing is unavailable, the website displays “Awaiting publication.”

The current version is intended for **desktop Chrome**. A Firefox version is in development. Compatibility with other Chromium browsers is not guaranteed.

## What this repository is for

Use this issue tracker for:

- Problems converting web pages to Markdown.
- Issues with the panel, Element Picker, Preview, or Settings.
- English and Russian interface translation issues.
- Feature requests and usability improvements.
- Questions about using Markdown-It.

Before opening an issue, check the [existing issues](https://github.com/dmitry-osin/markdown-it-issues/issues) to see whether the topic has already been reported.

## Reporting a bug

[Open an issue](https://github.com/dmitry-osin/markdown-it-issues/issues/new) and include:

1. **Problem:** a brief description of what went wrong.
2. **Steps to reproduce:** the actions you took, the selected content source, and the command used — Copy, Download, or Preview.
3. **Expected and actual results:** what you expected and what happened instead.
4. **Environment:** your Markdown-It version, browser version, and operating system.
5. **Example:** a page URL or a small reproducible HTML example, Markdown output, or a screenshot that helps explain the problem.

If the issue only occurs with a particular site profile or cleanup rule, mention that in your report.

## Requesting a feature

Describe the task you want to accomplish, what currently makes it difficult, and the behavior you would like to see. A concrete use case helps explain the proposal.

## Known limitations

- Protected browser pages such as `chrome://` cannot be converted.
- Documents inside embedded `iframe` elements are not read.
- Markdown preserves content structure rather than a site's exact appearance. Complex tables and some formatting may use sanitized HTML; diagnostics describe conversion issues.
- Site profiles or rules may need updating after a site's layout changes.
- If the browser refuses clipboard access, use Preview or download the result as a `.md` file.

## Privacy

Conversion runs locally when you request it. The extension has no telemetry, analytics, advertising, or accounts. Profiles and settings are stored on your device; there is no automatic cloud sync.

Remote images in Preview are blocked until you click **Load images**. Your browser then requests them from their original hosts, which receive ordinary network request information, including your IP address and the image URL.

Read the full [Markdown-It privacy policy](https://dmitry-osin.github.io/md-it/policy?lang=en) for details.
