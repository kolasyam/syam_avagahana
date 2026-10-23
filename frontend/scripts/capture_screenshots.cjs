const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE_URL = 'http://127.0.0.1:8000';
const OUTPUT_DIR = path.resolve(__dirname, '..', '..', 'docs', 'screenshots');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function clickTabById(page, tabId) {
  const clicked = await page.evaluate((id) => {
    // Find button inside navbar
    const buttons = Array.from(document.querySelectorAll('nav button'));
    // Matching tab index or content
    for (const b of buttons) {
      const text = b.textContent.toLowerCase();
      if (
        (id === 'workspace' && text.includes('executive workspace')) ||
        (id === 'market' && text.includes('market intelligence')) ||
        (id === 'forecast' && text.includes('forecast')) ||
        (id === 'scenario' && text.includes('scenario lab')) ||
        (id === 'briefs' && text.includes('decision briefs')) ||
        (id === 'sources' && text.includes('data fabric')) ||
        (id === 'upload' && text.includes('data intake')) ||
        (id === 'inspector' && text.includes('audit trail'))
      ) {
        b.click();
        return true;
      }
    }
    return false;
  }, tabId);

  await sleep(1500);
  return clicked;
}

async function run() {
  console.log(`Starting automated screenshot capture targeting: ${BASE_URL}`);
  console.log(`Output directory: ${OUTPUT_DIR}`);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1920,1080', '--disable-gpu']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  // 1. Initial Load - Executive Workspace
  console.log('Capturing 01_executive_workspace_command_center.png...');
  await page.goto(BASE_URL, { waitUntil: 'networkidle2' });
  await sleep(2500);
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01_executive_workspace_command_center.png') });

  // 2. Workspace lower scroll (recent briefs & alerts)
  console.log('Capturing 02_workspace_recent_briefs_and_alerts.png...');
  await page.evaluate(() => window.scrollTo(0, 480));
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '02_workspace_recent_briefs_and_alerts.png') });

  // 3. Market Intelligence Overview
  console.log('Capturing 03_market_intelligence_mandi_overview.png...');
  await clickTabById(page, 'market');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1000);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '03_market_intelligence_mandi_overview.png') });

  // 4. Market Intelligence Filter & Spreads
  console.log('Capturing 04_market_intelligence_filter_and_arrivals.png...');
  await page.evaluate(() => window.scrollTo(0, 500));
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04_market_intelligence_filter_and_arrivals.png') });

  // 5. Forecast & Risk - Multi-Horizon & Conformal Bands
  console.log('Capturing 05_forecast_multi_horizon_conformal_bands.png...');
  await clickTabById(page, 'forecast');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1200);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '05_forecast_multi_horizon_conformal_bands.png') });

  // 6. Forecast Risk Gauge & Drivers
  console.log('Capturing 06_forecast_risk_gauge_and_spike_probability.png...');
  await page.evaluate(() => window.scrollTo(0, 520));
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '06_forecast_risk_gauge_and_spike_probability.png') });

  // 7. Scenario Lab - Policy Simulation
  console.log('Capturing 07_scenario_lab_policy_simulation_studio.png...');
  await clickTabById(page, 'scenario');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1200);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '07_scenario_lab_policy_simulation_studio.png') });

  // 8. Scenario Lab - Fiscal Impact
  console.log('Capturing 08_scenario_lab_fiscal_exchequer_impact.png...');
  await page.evaluate(() => window.scrollTo(0, 480));
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '08_scenario_lab_fiscal_exchequer_impact.png') });

  // 9. Decision Briefs
  console.log('Capturing 09_decision_briefs_autonomous_recommendations.png...');
  await clickTabById(page, 'briefs');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1200);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '09_decision_briefs_autonomous_recommendations.png') });

  // 10. Governance Approval State Machine
  console.log('Capturing 10_governance_approval_state_machine.png...');
  await page.evaluate(() => window.scrollTo(0, 450));
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '10_governance_approval_state_machine.png') });

  // 11. Data Fabric
  console.log('Capturing 11_data_fabric_multi_source_orchestration.png...');
  await clickTabById(page, 'sources');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1200);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '11_data_fabric_multi_source_orchestration.png') });

  // 12. Data Fabric Ingestion Status
  console.log('Capturing 12_data_fabric_ingestion_health_status.png...');
  await page.evaluate(() => window.scrollTo(0, 450));
  await sleep(800);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '12_data_fabric_ingestion_health_status.png') });

  // 13. Data Intake / Client Studio
  console.log('Capturing 13_data_intake_client_studio_upload.png...');
  await clickTabById(page, 'upload');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1200);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '13_data_intake_client_studio_upload.png') });

  // 14. Run Inspector & Audit Trail
  console.log('Capturing 14_audit_trail_agent_execution_inspector.png...');
  await clickTabById(page, 'inspector');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1200);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '14_audit_trail_agent_execution_inspector.png') });

  // 15. Responsive Tablet View (768 x 1024)
  console.log('Capturing 15_responsive_tablet_view_768px.png...');
  await page.setViewport({ width: 768, height: 1024, deviceScaleFactor: 1 });
  await clickTabById(page, 'workspace');
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1000);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '15_responsive_tablet_view_768px.png') });

  // 16. Responsive Mobile View (375 x 812)
  console.log('Capturing 16_responsive_mobile_view_375px.png...');
  await page.setViewport({ width: 375, height: 812, deviceScaleFactor: 1 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(1000);
  await page.screenshot({ path: path.join(OUTPUT_DIR, '16_responsive_mobile_view_375px.png') });

  await browser.close();
  console.log('All 16 high-resolution screenshots captured successfully!');
}

run().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
