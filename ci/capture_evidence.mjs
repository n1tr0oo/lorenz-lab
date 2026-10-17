// Capture the actual Jenkins interface and the deployed Lorenz demo.
import { createRequire } from 'node:module';
import fs from 'node:fs';
const require = createRequire(process.env.PLAYWRIGHT_MODULE + '/package.json');
const { chromium } = require('playwright');
const dest = 'docs/assignment5/evidence';
const build = JSON.parse(fs.readFileSync(dest + '/provenance.json')).jenkins_build;
const browser = await chromium.launch({headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 1000}, deviceScaleFactor: 1.5});
const jobUrl = 'http://127.0.0.1:8080/job/lorenz-lab/';
await page.goto(jobUrl, {waitUntil: 'networkidle'});
const stageHref = await page.getByRole('link', {name: 'Full Stage View', exact: true}).getAttribute('href');
if (!stageHref) throw new Error('Jenkins did not expose the stage-view link');
const stageUrl = new URL(stageHref, jobUrl).href;
const pages = [
  ['01-jenkins-pipeline.png', stageUrl],
  ['02-jenkins-build.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/`],
  ['03-jenkins-tests.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/testReport/`],
  ['04-build-artifacts.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/artifact/results/run-1/`],
  ['05-test-deployment.png', 'http://127.0.0.1:8090/'],
  ['06-repeat-experiment.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/artifact/reports/repeatability.json`],
  ['07-run-manifest.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/artifact/results/run-1/manifest.json`],
  ['08-docker-image.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/artifact/reports/image-inspect.json`],
];
const captures = [];
for (const [name, url] of pages) {
  const response = await page.goto(url, {waitUntil: 'networkidle', timeout: 60000});
  if (!response || response.status() >= 400) throw new Error(`Cannot capture ${url}: HTTP ${response?.status()}`);
  if (name === '01-jenkins-pipeline.png') {
    await page.getByText('Repeat experiment', {exact: true}).first().waitFor();
  }
  if (url.endsWith('.json')) {
    await page.evaluate(() => { document.body.style.zoom = '150%'; });
  }
  if (name === '05-test-deployment.png') {
    await page.locator('#download-csv').waitFor({state: 'visible'});
    await page.waitForFunction(() => !document.getElementById('download-csv').disabled);
  }
  await page.screenshot({path: `${dest}/${name}`, fullPage: false});
  captures.push({file: name, url: page.url(), http_status: response.status()});
}
fs.writeFileSync(dest + '/screenshots.json', JSON.stringify(captures, null, 2) + '\n');
await browser.close();
