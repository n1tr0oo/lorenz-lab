// Capture the actual Jenkins interface and the deployed Lorenz demo.
import { createRequire } from 'node:module';
import fs from 'node:fs';
const require = createRequire(process.env.PLAYWRIGHT_MODULE + '/package.json');
const { chromium } = require('playwright');
const dest = 'docs/assignment5/evidence';
const build = JSON.parse(fs.readFileSync(dest + '/provenance.json')).jenkins_build;
const browser = await chromium.launch({headless: true});
const page = await browser.newPage({viewport: {width: 1440, height: 1000}, deviceScaleFactor: 1.5});
const pages = [
  ['01-jenkins-pipeline.png', 'http://127.0.0.1:8080/job/lorenz-lab/'],
  ['02-jenkins-build.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/`],
  ['03-jenkins-tests.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/testReport/`],
  ['04-build-artifacts.png', `http://127.0.0.1:8080/job/lorenz-lab/${build}/artifact/`],
  ['05-test-deployment.png', 'http://127.0.0.1:8090/'],
];
for (const [name, url] of pages) {
  await page.goto(url, {waitUntil: 'networkidle', timeout: 60000});
  if (name === '05-test-deployment.png') {
    await page.locator('#download-csv').waitFor({state: 'visible'});
    await page.waitForFunction(() => !document.getElementById('download-csv').disabled);
  }
  await page.screenshot({path: `${dest}/${name}`, fullPage: false});
}
await browser.close();
