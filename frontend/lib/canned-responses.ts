export function getResponse(input: string): string {
  const lower = input.toLowerCase();

  if (lower.includes('stock') || lower.includes('inventory') || lower.includes('material')) {
    return 'Current inventory levels: Cement (500 bags), Steel Rebar (12 tons), Bricks (8,000 units). Low stock alert for PVC pipes on Site B.';
  }

  if (lower.includes('budget') || lower.includes('cost') || lower.includes('finance')) {
    return 'Total budget across active sites is ₹1,45,00,000 with ₹98,50,000 spent to date (~68% utilized).';
  }

  if (lower.includes('equipment') || lower.includes('machinery')) {
    return 'Equipment status: Excavator #1 (Active - Site A), Tower Crane (Active - Site B), Concrete Mixer #2 (Under Maintenance).';
  }

  if (lower.includes('task') || lower.includes('schedule') || lower.includes('progress')) {
    return '14 tasks completed this week across 3 sites. Milestone "Foundation Concrete Pour" scheduled for Friday.';
  }

  if (lower.includes('alert') || lower.includes('warning') || lower.includes('delay')) {
    return '2 high-priority alerts: Weather delay risk on Metro Tower Site; Steel delivery delayed by 2 days.';
  }

  return `I have logged your query: "${input}". How else can I assist with your construction site management today?`;
}
