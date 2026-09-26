const { SupervisorClient } = require('./extension/client/supervisorClient');

async function test() {
  const client = new SupervisorClient(8765);
  const health = await client.checkHealth();
  console.log('Client checkHealth:', health);

  // Record marker
  await client.recordMarker('tests/sample_code.py', 8);

  // Dispatch Explain task
  const explainResult = await client.dispatchTask('explain', {
    filePath: 'tests/sample_code.py',
    line: 8,
    selectedCode: 'final_price = price - (price * discount_percent)',
    surroundingCode: 'def calculate_discount(price):\n    final_price = price - (price * discount_percent)',
    language: 'python'
  });
  console.log('Explain verdict:', explainResult.supervisorVerdict);
  console.log('Explain agent:', explainResult.agent, 'status:', explainResult.status);

  // Dispatch Debug task
  const debugResult = await client.dispatchTask('debug', {
    filePath: 'tests/sample_code.py',
    line: 13,
    selectedCode: 'result = a / b',
    surroundingCode: 'def risky_divide(a, b):\n    result = a / b',
    language: 'python'
  });
  console.log('Debug verdict:', debugResult.supervisorVerdict);
  console.log('Debug suggestedFix:\n', debugResult.debugData?.suggestedFix);

  // Fetch events
  const events = await client.getEvents();
  console.log('Events count:', events.events?.length);
  console.log('Latest event:', events.events?.slice(-1)[0]?.message);
}

test().catch(console.error);
