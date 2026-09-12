import type { Memory, Source, Topic, TopicDetail, Update } from './models.ts';

// Fictional snapshot for repeatable demos. Dates and IDs intentionally stay fixed.
function source(id: string, author: string, channel: string, receivedAt: string, originalText: string): Source {
  return { messageId: `sample-${id}`, service: 'Slack', author, channel, receivedAt, originalText, sample: true };
}
function memory(id: string, text: string, type: 'idea' | 'decision' | 'question' | 'fact', original: Source): Memory {
  return { id, text, type, source: original };
}
function topic(id: string, name: string, category: 'Product' | 'Personal', description: string, summary: string, memories: Memory[]): TopicDetail {
  return { topic: { id, name, categoryId: category.toLowerCase(), category, description, memoryCount: memories.length },
    summaryKind: 'AI overview', summary, memories };
}

// Author each original once: shared sources retain all context across topics.
const kickoff = source('onboarding-kickoff', 'Alex Chen', '#product', '2026-09-01T16:15:00Z',
  'Idea for Atlas onboarding: try a three-step checklist — connect Slack, save one useful message, then explore its topic. In last week’s five sessions, three people connected Slack but never saved anything. Separately, for the camping trip on September 19, could we borrow Maya’s tent? I’ll move the logistics to #weekend-plans.');
const pilot = source('onboarding-pilot', 'Priya Shah', '#product', '2026-09-02T17:30:00Z',
  'Decision from planning: pilot the checklist with five new users. Alex owns the prototype; Maya will recruit. Success means at least four of five save a message and open its topic without a facilitator. Keep the existing onboarding available until we review the sessions.');
const results = source('pilot-results', 'Maya Torres', '#customer-research', '2026-09-08T20:10:00Z',
  'Five pilot sessions are complete. Four people saved a message and opened its topic without help; one needed a hint at the permissions screen. Median time to first saved message was 3m 40s. This is a small usability sample, not evidence of a conversion lift. Two people asked whether private-channel content would become visible to everyone.');
const rollout = source('pilot-followup', 'Alex Chen', '#product', '2026-09-10T18:45:00Z',
  'The checklist met our four-of-five usability target. Decision: keep it with the pilot group while we rewrite the permissions explanation; no general rollout yet. Priya reviews the copy September 14. Open question: should admins see a separate permissions preview before connecting Slack?');
const priceIdea = source('pricing-idea', 'Jordan Ellis', '#pricing', '2026-09-01T19:20:00Z',
  'For Atlas pricing, I’d like to test a $12 per active user monthly Team plan, billed monthly. Active means someone who saves or explores context that month. This is a proposal for interviews, not a price change. We still need an answer for admins who never open the reader.');
const priceResearch = source('pricing-research', 'Maya Torres', '#pricing', '2026-09-04T18:05:00Z',
  'Pricing interviews: four of six team leads preferred a predictable workspace bill; two preferred per-user pricing. Three could not forecast active users month to month. These are six exploratory interviews, not a market-wide willingness-to-pay estimate.');
const priceDecision = source('pricing-decision', 'Priya Shah', '#pricing', '2026-09-09T17:20:00Z',
  'Decision: compare the $12-per-active-user concept with a flat $99/month workspace concept capped at 10 users in six more interviews. Jordan owns the script for September 15. No checkout changes or public price announcement until we review the results.');
const priceQuestion = source('pricing-admin', 'Jordan Ellis', '#pricing', '2026-09-11T16:35:00Z',
  'Still unresolved for the interview script: does a read-only admin count toward the 10-user workspace cap? I’m leaving that as an explicit question rather than implying unlimited seats.');
const recruiting = source('research-plan', 'Maya Torres', '#customer-research', '2026-09-02T16:40:00Z',
  'Research plan: recruit six team leads from agencies with 10–50 people for 30-minute interviews. Four are confirmed, two pending. Get separate consent for recording. I’ll remove client names from the notes before sharing them in #product.');
const findings = source('research-findings', 'Maya Torres', '#customer-research', '2026-09-07T19:00:00Z',
  'All six team-lead interviews are complete. The recurring job was finding why a decision changed, not just the final answer. Five participants described searching old Slack threads before a client handoff. Idea: show a changed decision, with both original messages visible, in the launch walkthrough.');
const launch = source('launch-scope', 'Priya Shah', '#launch', '2026-09-03T17:00:00Z',
  'Decision: aim for an invite-only Atlas preview on September 22 with eight design-partner workspaces. Scope is Slack capture plus the read-only topic explorer. Public signup and billing are excluded. The date is conditional on permissions QA and the source-inspection review.');
const readiness = source('launch-readiness', 'Sam Okafor', '#launch', '2026-09-09T20:30:00Z',
  'Preview readiness: walkthrough draft and support rota are ready. Permissions QA is still open; Leo owns the September 16 review. Jordan will draft partner invitations, but do not send until Priya gives the go-ahead. Can each partner nominate an admin before the September 18 rehearsal?');
const walkthrough = source('launch-walkthrough', 'Jordan Ellis', '#launch', '2026-09-11T21:00:00Z',
  'Walkthrough idea: open onboarding, expand the pilot result, then compare the pricing proposal with the later decision. Close by opening the camping question from the same original message to show context spanning two topics. Use fictional sample data throughout the recording.');
const searchFinding = source('search-finding', 'Leo Martin', '#product', '2026-09-04T16:20:00Z',
  'Two participants typed “who approved this?” into the topic-name filter and got no results. It matches topic names, not memory content. Idea: make the placeholder explicit and keep matching consistent in Universe and List.');
const searchDecision = source('search-decision', 'Alex Chen', '#product', '2026-09-08T17:05:00Z',
  'Decision: use “Find topics by name” and keep matching case-insensitive. No conversational question box in the web preview; questions stay in Slack. Leo will check empty results and clearing the filter during September 16 QA.');
const searchQuestion = source('search-alias', 'Maya Torres', '#product', '2026-09-10T16:50:00Z',
  'Should “setup” eventually find “Atlas onboarding” through topic aliases? This remains a research question. For the preview, keep literal topic-name matching so we can explain it accurately.');
const provenance = source('source-review', 'Sam Okafor', '#engineering', '2026-09-03T19:15:00Z',
  'The current topic API returns source IDs and received timestamps, but no original message body, author, or channel. An extracted memory is not an original quote. Decision: show “Original text unavailable” when the body is absent.');
const sourceRules = source('source-rules', 'Leo Martin', '#engineering', '2026-09-07T17:40:00Z',
  'Agreed: label ingestion timestamps “Received”; only show an external source link when the API supplies a valid HTTP(S) URL. Never construct a Slack permalink from a message ID. Fixture quotes can be expanded but must carry the Sample source label.');
const sourceAccess = source('source-access', 'Sam Okafor', '#engineering', '2026-09-11T18:25:00Z',
  'Backend follow-up for September 16: can original text be returned with the same access checks as its source channel? Still open. The preview must handle missing originals even if the endpoint gains optional fields.');
const tent = source('camping-tent', 'Maya Torres', '#weekend-plans', '2026-09-03T20:00:00Z',
  'Yes, Alex can borrow my three-person tent for September 19–20. It fits two comfortably with bags. I’ll bring the footprint and poles to the office Friday, September 18; please return everything dry on Monday.');
const camping = source('camping-plan', 'Alex Chen', '#weekend-plans', '2026-09-09T19:10:00Z',
  'Five people confirmed for September 19–20. Sam will bring a second tent, so there is space for everyone. Let’s leave the office at 8:00 Saturday morning. Campsite booking is still pending — I’ll confirm before anyone buys food.');
const rain = source('camping-rain', 'Sam Okafor', '#weekend-plans', '2026-09-11T19:30:00Z',
  'Can we agree on a rain fallback by Thursday, September 17? My suggestion is a day hike plus dinner if the forecast looks bad. Only a backup idea; do not cancel the overnight plan yet.');
const dinnerPoll = source('dinner-poll', 'Jordan Ellis', '#team-social', '2026-09-04T20:00:00Z',
  'Dinner after the September 18 rehearsal: seven people voted for 6:30 pm. Two need vegetarian options and one asked for a quiet table. I’ll look for somewhere near the office. Nothing is booked yet.');
const dinnerBudget = source('dinner-budget', 'Priya Shah', '#team-social', '2026-09-10T20:15:00Z',
  'Decision: dinner budget is $35 per person for seven people, excluding transport. Jordan will check a vegetarian-friendly menu and availability at 6:30 pm on September 18. Reservation still unconfirmed.');
const dinnerAccess = source('dinner-access', 'Jordan Ellis', '#team-social', '2026-09-11T20:20:00Z',
  'Before I book: does anyone need a step-free entrance or have food allergies beyond the vegetarian requests? Reply privately if you prefer; I’ll share only what the venue needs.');
const runIdea = source('running-idea', 'Leo Martin', '#running-club', '2026-09-02T19:30:00Z',
  'Idea: relaxed 5 km loops on Wednesdays at 7:30 am from the office. Regroup at every turn; walkers can take a shorter loop. No need to track pace.');
const runPlan = source('running-plan', 'Maya Torres', '#running-club', '2026-09-08T19:35:00Z',
  'Decision: first run September 16. Meet at the office entrance at 7:30 am; leave at 7:35. I’ll lead the shorter walking loop and Leo the 5 km route. Check weather the evening before.');
const runQuestion = source('running-coffee', 'Leo Martin', '#running-club', '2026-09-11T17:15:00Z',
  'For September 16, coffee afterwards or a hard finish at 8:15? No decision yet. I can adjust the route once we know who has an early meeting.');
const bookIdea = source('book-idea', 'Sam Okafor', '#book-club', '2026-09-05T17:00:00Z',
  'Idea for book club: The Design of Everyday Things. Bring one confusing everyday object as an example; no need to finish the whole book. Would September 24 at lunch work?');
const bookPlan = source('book-plan', 'Priya Shah', '#book-club', '2026-09-10T19:00:00Z',
  'Decision: book club September 24, 12:15–1:00 pm in the small meeting room. Focus on the first two chapters of The Design of Everyday Things. Sam facilitates; bring lunch and an example of a confusing interface.');

const dataset: TopicDetail[] = [
  topic('atlas-onboarding', 'Atlas onboarding', 'Product', 'First-run setup, Slack permissions, and the five-user checklist pilot.',
    'The checklist reached its usability target: four of five users saved a message and opened its topic unaided. It remains in the pilot while permissions copy is revised. An admin permissions preview is still an open question.', [
      memory('onboarding-idea', 'Try a three-step checklist: connect Slack, save a message, then explore its topic.', 'idea', kickoff),
      memory('onboarding-decision', 'Pilot with five new users; success is four completing the flow without help.', 'decision', pilot),
      memory('onboarding-baseline', 'Three of five participants in earlier sessions connected Slack but never saved a message.', 'fact', kickoff),
      memory('onboarding-owners', 'Alex owns the prototype; Maya owns pilot recruitment.', 'decision', pilot),
      memory('onboarding-result', 'Four of five pilot users completed the flow unaided; median time to first save was 3m 40s.', 'fact', results),
      memory('onboarding-permissions', 'Two pilot users asked whether private-channel content would become visible to everyone.', 'fact', results),
      memory('onboarding-rollout', 'Keep the checklist in the pilot while permissions copy is revised; Priya reviews September 14.', 'decision', rollout),
      memory('onboarding-admin', 'Should admins see a separate permissions preview before connecting Slack?', 'question', rollout),
    ]),
  topic('atlas-pricing', 'Atlas pricing', 'Product', 'Pricing interviews, billing concepts, and unresolved seat rules.',
    'The initial $12-per-active-user proposal raised predictability concerns in six exploratory interviews. The team will compare it with $99/month for up to 10 users. Neither concept is approved for launch; admin seat treatment remains unresolved.', [
      memory('pricing-idea', 'Test a $12 per active user monthly Team plan in interviews.', 'idea', priceIdea),
      memory('pricing-definition', 'Define active users as people who save or explore context during the month.', 'idea', priceIdea),
      memory('pricing-feedback', 'Four of six team leads preferred predictable workspace billing; two preferred per-user pricing.', 'fact', priceResearch),
      memory('pricing-comparison', 'Compare $12 per active user with $99/month for up to 10 users in six more interviews.', 'decision', priceDecision),
      memory('pricing-hold', 'Jordan owns the September 15 script; checkout changes and public pricing announcements are on hold.', 'decision', priceDecision),
      memory('pricing-admin', 'Does a read-only admin count toward the 10-user workspace cap?', 'question', priceQuestion),
    ]),
  topic('camping-trip', 'Camping trip', 'Personal', 'September 19–20 camping plans, shared tents, and weather fallback.',
    'Maya confirmed Alex can borrow her tent, and Sam will bring a second tent for five campers. Departure is proposed for 8:00 am September 19. The campsite booking and rain fallback are still unresolved.', [
      memory('camping-question', 'Could Alex borrow Maya’s tent for the September 19 camping trip?', 'question', kickoff),
      memory('camping-tent', 'Maya agreed to lend her tent; pickup September 18, return dry on Monday.', 'fact', tent),
      memory('camping-plan', 'Five campers are confirmed; Sam will bring a second tent. The campsite booking is pending.', 'fact', camping),
      memory('camping-rain', 'Can the group agree on a rain fallback by September 17?', 'question', rain),
    ]),
  topic('customer-discovery', 'Customer discovery', 'Product', 'Agency interviews and why people revisit old decisions.',
    'Six agency team-lead interviews are complete. Five described searching old Slack threads before client handoffs. Explaining why decisions changed was a recurring need; a walkthrough showing that evolution is proposed.', [
      memory('research-plan', 'Recruit six team leads from agencies with 10–50 people for 30-minute interviews.', 'decision', recruiting),
      memory('research-consent', 'Get separate recording consent and remove client names before sharing notes.', 'decision', recruiting),
      memory('research-complete', 'All six interviews are complete; five participants searched Slack before client handoffs.', 'fact', findings),
      memory('research-job', 'Understanding why a decision changed was a recurring need in the interviews.', 'fact', findings),
      memory('research-demo', 'Show a changed decision with both original messages in the walkthrough.', 'idea', findings),
    ]),
  topic('preview-launch', 'Preview launch', 'Product', 'Eight design partners, preview scope, and readiness checks.',
    'The invite-only preview targets September 22 for eight workspaces, conditional on permissions QA and source review. The walkthrough and support rota are ready. Invitations await approval.', [
      memory('launch-date', 'Target September 22 for eight design partners, conditional on permissions QA and source review.', 'decision', launch),
      memory('launch-scope', 'Include Slack capture and the read-only explorer; exclude public signup and billing.', 'decision', launch),
      memory('launch-readiness', 'Walkthrough and rota are ready; permissions QA is due September 16. Invitations await approval.', 'fact', readiness),
      memory('launch-demo', 'Demo onboarding evidence, evolving pricing decisions, and a source shared with the camping topic.', 'idea', walkthrough),
    ]),
  topic('topic-search', 'Topic search', 'Product', 'Name filtering, empty results, and possible topic aliases.',
    'Two participants mistook the filter for a question interface. The preview uses explicit copy and case-insensitive topic-name matching. Aliases remain a research question.', [
      memory('search-confusion', 'Two participants tried asking “who approved this?” in the topic-name filter.', 'fact', searchFinding),
      memory('search-copy', 'Label the filter “Find topics by name” and keep matching case-insensitive.', 'decision', searchDecision),
      memory('search-boundary', 'Conversational questions stay in Slack; no web question box in the preview.', 'decision', searchDecision),
      memory('search-alias', 'Should “setup” eventually find Atlas onboarding through a topic alias?', 'question', searchQuestion),
    ]),
  topic('source-traceability', 'Source traceability', 'Product', 'Original-message availability, source links, and access checks.',
    'The API currently omits original text, authors, and channels. The reader must identify missing originals, label ingestion times Received, and use supplied source URLs. Access checks for original text remain an open backend question.', [
      memory('source-missing', 'Show “Original text unavailable” when the body is absent; never substitute an extracted memory.', 'decision', provenance),
      memory('source-links', 'Label ingestion times Received and use supplied HTTP(S) URLs; never guess Slack permalinks.', 'decision', sourceRules),
      memory('source-access', 'Can original text be returned with the same access checks as its source channel?', 'question', sourceAccess),
    ]),
  topic('team-dinner', 'Team dinner', 'Personal', 'September 18 rehearsal dinner, dietary needs, budget, and booking.',
    'Seven people preferred 6:30 pm after the rehearsal. The budget is $35 each excluding transport, with vegetarian options needed. Jordan is checking availability and access needs; the reservation is unconfirmed.', [
      memory('dinner-preferences', 'Seven people preferred 6:30 pm; two requested vegetarian options and one a quiet table.', 'fact', dinnerPoll),
      memory('dinner-budget', 'Set a $35-per-person budget for seven people; Jordan will check menu and availability.', 'decision', dinnerBudget),
      memory('dinner-access', 'Does anyone need a step-free entrance or have additional food allergies before booking?', 'question', dinnerAccess),
    ]),
  topic('running-club', 'Running club', 'Personal', 'Wednesday morning runs with a shorter walking option.',
    'The first run is September 16, meeting at 7:30 am outside the office. Leo leads the 5 km route and Maya the walking loop. Coffee afterwards versus an 8:15 finish is undecided.', [
      memory('running-idea', 'Try relaxed Wednesday 5 km loops with regrouping stops and a shorter walking route.', 'idea', runIdea),
      memory('running-plan', 'Start September 16: meet 7:30, leave 7:35; Leo leads runners and Maya leads walkers.', 'decision', runPlan),
      memory('running-coffee', 'Should the September 16 run finish with coffee or end by 8:15?', 'question', runQuestion),
    ]),
  topic('book-club', 'Book club', 'Personal', 'A lunchtime discussion of everyday design and confusing interfaces.',
    'Discuss chapters one and two of The Design of Everyday Things on September 24, 12:15–1:00 pm, in the small meeting room. Sam facilitates; bring lunch and an example of a confusing interface.', [
      memory('book-idea', 'Read The Design of Everyday Things and bring a confusing everyday object as an example.', 'idea', bookIdea),
      memory('book-plan', 'Meet September 24, 12:15–1:00 pm, for chapters one and two in the small meeting room; Sam facilitates.', 'decision', bookPlan),
    ]),
];

export const fixtureTopics: Topic[] = dataset.map(detail => detail.topic);
const details = new Map(dataset.map(detail => [detail.topic.id, detail]));
export const fixtureUpdates: Update[] = ['preview-launch', 'atlas-pricing', 'camping-trip'].map(id => ({
  topicId: id, topicName: details.get(id)!.topic.name, label: 'Updated',
  note: 'Sample · Slack · 1 new memory saved', sample: true,
}));
export function sampleDetails(id: string, selectedTopic: Topic): TopicDetail {
  const original = details.get(id);
  if (original) return structuredClone({ ...original, topic: selectedTopic });
  return { topic: selectedTopic, summaryKind: 'AI overview', summary: 'A sample topic used to check the exploration layout.',
    memories: [memory(`memory-${id}`, 'Review the checklist in the next project discussion.', 'idea',
      source(`qa-${id}`, 'Alex Chen', '#product', '2026-09-12T16:00:00Z', 'Let’s review the checklist in our next project discussion.'))] };
}
export function scenarioTopics(scenario: string): Topic[] {
  if (scenario === 'empty') return [];
  if (scenario === 'crowded') return [...fixtureTopics, ...Array.from({ length: 40 }, (_, i) => ({
    ...fixtureTopics[i % 3], id: `extra-${i}`, name: `Atlas research topic ${i + 1}`, memoryCount: 1,
  }))];
  if (scenario === 'long') return fixtureTopics.map((t, i) => i === 0 ? { ...t, name: 'Atlas onboarding research and accessibility improvements for international teams across multiple projects' } : t);
  return fixtureTopics;
}
