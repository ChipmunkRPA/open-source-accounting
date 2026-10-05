// Reviewed immutable reader bindings. Update only alongside the exact reader index and tests.
export type PinnedReaderArticle = {canonical_version:string;canonical_sha256:string;reader_sha256:string;title:string;creator_credit:string;license:string};
export const READER_EDITION = "2026-10-05.1";
export const READER_NOTICE = "**Reader edition 2026-10-05.1** · Wording changes are limited to labels and notices. Earlier check statements refer to the original article revision. No new professional review or source verification is claimed.";
export const CANONICAL_MANIFEST_SHA256 = "46375749261374b28bf4b114e59ad8709c5809a538d52d5efbfe705c918b190b";
export const READER_RULES_SHA256 = "67742a9c5472e0783c0a6b3cc393b3206fd9bf931fadcf70c1da2d0da89f31a1";
export const READER_ARTICLES:Readonly<Record<string,Readonly<PinnedReaderArticle>>> = {
  "authority-and-period": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "0bfaa27a31e0abc364455a814adbf21876ff0bf55eda457754e138d11f294743",
    "reader_sha256": "f2214b49c062deabaf0ac15e4a4558c392a7f2220e4c640a9cb04742537dbc5c",
    "title": "Build an authority and reporting-period map",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "revenue-research-map": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "a6edcf13e48c1c63a6c95c5e51c23e89d3c0b39c23e9b169a9e29054ea778e00",
    "reader_sha256": "285a516bde63c076efd243745420f2ffc55745660671c9b4f6fc82b3761ed533",
    "title": "Revenue recognition: assemble the five-step evidence file",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "saas-implementation": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "9cb177e6ceb41c585b7cde7200d1382e42755680ee3c23b98c87b7d973ad92e5",
    "reader_sha256": "d27395be064f8042a6892add541d098a177c21b61ec41fb122aa5d2d1ce2a8dd",
    "title": "SaaS implementation fees: investigate the promise before the price",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "customer-payments": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "76c02cc5ccc58bd6541d9f0ce68703fd0550f34eabe26bc91fef814c33bbef50",
    "reader_sha256": "4d5b5166a88d9de2e507e7223ad20243e61767c513352247547462e1765619f0",
    "title": "Payments to customers: route the arrangement before choosing an expense account",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "lease-identification": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "352bb93d8471f2a0a003d2c1baa50d9a53a89c043ff8aa0d9d16ee0ba34ab4d5",
    "reader_sha256": "7c76750504e5a067c9ba7ed997a14d37fe44efa37c86f46ae73b4561299e91d9",
    "title": "Lease identification: examine assets, substitution, and decision rights",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "lease-measurement": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "4dd251fafb6c9b45ae5ffb7ec9f0d51035abf623d8c2d8f0303f9e0b95fd46df",
    "reader_sha256": "43510317daa17880fa88b4065209ba856514ddb9b96a527de9a45c8e575dca93",
    "title": "Lessee measurement: reconcile inputs before calculating",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "share-based-award-intake": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "b90c0ba452422960ada6c7e9ebc41d5ad8d49b3ac0dc90518c9e26930e4f044d",
    "reader_sha256": "79b43df75a37ccdd19b821d927a0a1b443194c42cefcf685dabe4291dea847e6",
    "title": "Share-based awards: reconcile the register before choosing a model",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "loss-contingencies": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "7b1c04fb96f9d150491d12b3a7fe84901a5738649cb3981641b21b04cc40faa9",
    "reader_sha256": "c51d2aea218679d44df9ece42934768307301a193cc1ee13d217348a0799a336",
    "title": "Loss contingencies: recognition, disclosure, and classification are separate questions",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "materiality": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "0a687640e5b7dc25484f4c0a775671d11aad640a5073f253efe4dd3c9ec47f82",
    "reader_sha256": "59e25ce55a714d4314f37548aeb26b3f3d724b5fb4d8d07ba47abddf05bf504f",
    "title": "Materiality: use a threshold to begin the analysis, not end it",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "error-measurement": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "fd1097006a9e64e4fdb729bc81313158b175fbbb2a31fff7f5ff8d8c3df47ced",
    "reader_sha256": "12fdf1b361c530101056c754ccf98730f76aeee13eab661a4acd58e359b7b245",
    "title": "Misstatement measurement: reconcile current-year effects and accumulated balances",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "icfr-deficiencies": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "b22d4f457b8806655bbaa3ff459454714b471e8535586d42ea37061a4017f511",
    "reader_sha256": "57d7c307193b0aeb3beeced7217fbf5c203869ec18e45a69cb30ff3b5011d8e9",
    "title": "ICFR deficiencies: evaluate potential exposure and remediation evidence",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "electronic-audit-evidence": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "9553a213000c05a06d7dea5c6b1235fc03b8317f6a4b0df4206a3ba3e8b00d2e",
    "reader_sha256": "6810283156476ddb53d0648151e41a558d0ebfc9d94e66c2de6facd0a2f11ba3",
    "title": "Electronic audit evidence: trace the data before trusting the analysis",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "non-gaap-review": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "82bf79f9fae0bf1e44ad0aa6c14f8eeb1dd354f13ec5f6e29aab63b0c4d5a3ae",
    "reader_sha256": "738d95dc78822aea940aabfec31a0f19709e48cc7f73d3ba674649e1c0f44350",
    "title": "Non-GAAP measures: review the adjustment, label, reconciliation, and presentation",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "yellow-book-scope": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "24e66fd1bf33ba9d0899f77f125add692bb66ed335fa3f2e51a2a4499c8e7462",
    "reader_sha256": "662c8e7ca1284b872a6b13ff2576ba3e0e1a1b5db0202cebed065344ef66e76e",
    "title": "Government auditing: determine the Yellow Book engagement and version",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-ssp-allocation": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "dbe625a9de40b6ae716e718bdafc5e0aa1d8cde8ba6a96a46b165638e62c41c4",
    "reader_sha256": "3dd6509dea81e284542cf79695206828ec1b182f845175c5d1ddda3448d00502",
    "title": "Worked case: allocate a fixed price using confirmed standalone prices",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-lease-present-value": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "1b07da25dfc0fcb7d6e04870b159545a51bb9ebf3b55f5b3c3ec215244c61c93",
    "reader_sha256": "34924ec533812f8bd442454b7d14d3c4cb49c1cc27156e6dfee9994492b62a5b",
    "title": "Worked case: a three-payment present-value schedule",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-implementation-alternatives": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "2081a4f5be730d7bec3964ae597fb92e32aeb732bdcb77381795d0a2e9bd38bd",
    "reader_sha256": "8495d62d8552dedfe3b884ba2c04f6e02ff190f3faa376fab0b0b9b6c88b7c75",
    "title": "Worked case: the same implementation fee, different missing facts",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-accumulated-error": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "0dd8dcac3cc79523b86ec91780c303ac043699fa13e1cba9b136102901dd590b",
    "reader_sha256": "212567ca3b8744a7f0265298b2d58e201b9aab531dd3364c1102bbc4899c4693",
    "title": "Worked case: a liability error accumulates over three years",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-control-remediation": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "d666ec2a8c565f65621e828bc6fb1cb02fc6cdc837280a5d1b973d88ee40a89d",
    "reader_sha256": "29f63443bd824d96b138bb40b896da902f7ae54372ba77b76bea082021e1fcb4",
    "title": "Control remediation: separate reporting, operation and evidence dates",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "technical-memo-template": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "abf42dbac7d4041c78dcba53fb28a9598a66b2f059078fdba97a1d0d5301daac",
    "reader_sha256": "89e57c74238f0f0c26a74721a4af0c61a370ce95360fe2048209fabc8fcfef6e",
    "title": "Technical accounting memorandum",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "clause-evidence-template": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "9c4e589107441260a8dce40f1af2ef0487256ad9641404a5308a8dc50792de92",
    "reader_sha256": "15680b90bfb830db57a37e85cd18a71e2e592db06b5029af9dce9e4526e51096",
    "title": "Contract clause-to-criterion matrix",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "audit-evidence-template": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "cfbf9595c4c32fdbdc3a30a96c590edb1f118f42631ca26ec40bbef4951055c9",
    "reader_sha256": "16edad852a50589543ea9896b91ae5c665a9df09ab8e7b1efb1ce641f1861f44",
    "title": "Audit evidence request and procedure tracker",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "disclosure-review-template": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "3df8fd6653aea96920a476f6224c2f0a7264587b413e60b8d862bfd7f1e2abc6",
    "reader_sha256": "47a5617d687c28c815db9cab78123839e9b1dfe82ed04fb43bd37fa0e18b40a0",
    "title": "Disclosure review issue log",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "content-review-template": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "f4520e015cb6893187cf1919b02857a07cf20f74c330266d5be8d161da267551",
    "reader_sha256": "e32e4c21e167b173f54c9ce973ee2fa62c2cdcf22c30825902b749a1a3a7e84b",
    "title": "Technical and rights review for a contributed article",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "source-onboarding-template": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "0a05eade8ea3676d44666840614f3635e5b4f5b8105c4d17e2a42bfcd6c19778",
    "reader_sha256": "eed733c0bebffb8267499ea4e9a7bc256cd994536f6a9fbcffbe42e868e7fe33",
    "title": "Source onboarding and acquisition checklist",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-deep-research": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "b92eeecaa3a6a30904f4783a7f2ee19bba60f308ff03ed68e911552fbe157aef",
    "reader_sha256": "928b8a4e56766e3172e81575386d1e4921db5c8fe4b2a8e088d10a2afc9320a8",
    "title": "Deep research — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-memo": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "7db93e460bf5482ddd3f4d748f3ed4fae402e38d7be3cbe4a0c241e517ed96c5",
    "reader_sha256": "7be970a024c11af3b41ff476eb72781091df56ce55eec4b17fa76a51b3fa190c",
    "title": "Accounting memorandum — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-document-gaap": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "9ca1d3a7ba02a89e60bb5a4abb69eefeedb85328280d6a74193fe6e9d5e81806",
    "reader_sha256": "9c2763d667b4f0aeb6bb2c8c3ff6c8ae037d776466eb711200c59d468361a1a7",
    "title": "Uploaded documents plus GAAP — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-contract-compare": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "382a6fce10315d965a819f27922ff6573ab6d97b4fee99f897899ca664087385",
    "reader_sha256": "dd6444aea10ed1a4ccce62fe2acd2fce5f5f63fa404fbc19f15866960981647b",
    "title": "Contract and amendment comparison — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-memo-review": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "ecab5b34b537c489f90e24d126067890fae2e49c0dd62b140c64f91eccea1fcb",
    "reader_sha256": "b6969dd68f7bf43578b0c4de17cedc25428834b972566f8d724b7788120f601c",
    "title": "Challenge my memo — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-disclosure-review": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "e253a18c546bfaf740cfaa0f9e6f5754d2fcdc0fd5526394a6874415aab53aea",
    "reader_sha256": "66e923c605336f29d49aa2d6690e921ddad0ea0a169bc4f228e5b5cfe299cf8a",
    "title": "Disclosure gap review — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-policy-draft": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "1c768cbfc3c6ae2628e72c1e6176950b610e3d5c70a9f0c4911d6f89af941907",
    "reader_sha256": "63edbc2fd41337e4cc617e70f3316bb772d229128a6b28c5391b83925faa7cc2",
    "title": "Accounting policy drafting — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-revenue-workpaper": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "8ba8fb9c04bae0023c9bf12994765444d4dd931d0fbd75bd1c8a4808b9a58b24",
    "reader_sha256": "aa17b9608f7cff8de3b5635f7016b65e09815d234abe2e602e57c524bb07581d",
    "title": "Revenue contract workpaper — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-lease-workpaper": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "c4e9c0433a24a8a5009732cd8f57e1f76239c3d04820d33ecdab2aeb39b5ad2d",
    "reader_sha256": "ffb84ac5cbaf40d817908cb10a69f807f22222694cb0f3e4d6e5c15c486f4d21",
    "title": "Lease assessment and schedule — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-disclosure-benchmark": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "1b9f8b5beb47271c5c3fce0f68544319e3ab2481918928a48bc4303963e60ffa",
    "reader_sha256": "083301b6e05b7049853c3d475f7d2ef52e059214539af7aac051e8379a1d1ed8",
    "title": "Disclosure benchmarking — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-sec-response": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "52facd83f14f5e2b8b3e575d19c553984d92eba365108555533ad8f7a5e50b43",
    "reader_sha256": "5f16f0daa029b37a32e02645e5628cabfedbbe6df03bb9295ebb210a32567bee",
    "title": "SEC comment-response preparation — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-audit-prep": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "c43fa077daa0963372e59db72f661c836567ee77cd1e51ac4344b2033c2d4045",
    "reader_sha256": "47eb9b78f7c40b3c15f9ae123aca516f3496b2ecac79a18e7eec2e64f29e02bd",
    "title": "Audit preparation pack — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-controls-review": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "ebe9158a308adb6abd1df3f154517e55329fba2c98a6c521d14f9597e273aaac",
    "reader_sha256": "108d0d61e9b17e3f68db0f514e8b94517cfa8253a127c50abef0fd9e4a51786a",
    "title": "Control design and deficiency review — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-close-pack": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "bf76a908a09551ee9bc0542004afaeeec90548cf797fac14d535ed1bab67bbc6",
    "reader_sha256": "40c963f32346e3848a9863ed3b9e98488aa1185a38ddef4ec2c6ef5b34df1334",
    "title": "Close issue and evidence pack — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-framework-compare": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "b2462b4579d8cb67a2d171278c309a646ebbf78c6dced16e5daaf5f9b12eef15",
    "reader_sha256": "72b29f23df882d6c9926eaa69b756919c6ec3dcd6ec16f62bcab6d7b0949c279",
    "title": "U.S. GAAP and IFRS issue comparison — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "playbook-standards-watch": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "daff5ae23e1cf976dc4c6da783f2d6311e903577f883d8a743980f9eba13de1d",
    "reader_sha256": "21c2694d4a3abb13aaf20d125b1bf0e7b5ccbfae3a65d449bcf44555729364c8",
    "title": "Opt-in standards impact watch — Agent playbook",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "research-study-questions": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "e6bb5cea4459a478214e85e03024985e73fdb6717462bdb0d4e3d0978605b86e",
    "reader_sha256": "07d26c88a8f3075b6235f2cd4228125575061ab587edb4704212417ec4857574",
    "title": "30 research and accounting study questions",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "cash-flow-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "e45323f7759266d7b16ada741dbd4e110e00fb6b4a20cc7450334a6e208e3fa9",
    "reader_sha256": "3800735e47e17f6dbb1b37d9fea6d5f4c398e2424f6274d4e0c2c35f84cf9337",
    "title": "Cash flows: reconcile before classifying",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "receivable-loss-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "377f14b7de202f551bc32a220e6bcc46f9faf3d2c8792766fb3656ed69de4e54",
    "reader_sha256": "4377209a53bd2b6a6d4a6b5907455966531028ac50928cd8ca1cc04a2024b25c",
    "title": "Receivable losses: turn aging data into an evidence file",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "inventory-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "70bef72117b1dd31b904a73e8d269ccdaaf1e1f586ff086edc17ebd75096b071",
    "reader_sha256": "db658094ee552fba2f2b2eaa11a85cc649d96dc4ce9a5995e2987685084f9dab",
    "title": "Inventory: connect quantities, costing, and recoverability",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "impairment-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "586427813ea3d34e65f1bf1f6033411cf5cf443aff0b07c4daab7ae0d1c2519a",
    "reader_sha256": "756a43a84790af593e695d6e371b2f219375f61dd1acc2e77f1c73709dc8ca85",
    "title": "Impairment: choose the model before the valuation",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "fair-value-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "cf404f1a491599fb4ba07567f85487dae29b6f1f7673deb533eeeb24b6b86a6e",
    "reader_sha256": "47a996940901ff6059e741e7852a0a8d9f5d3a90c40247364958c350b1a435c2",
    "title": "Fair value: document the market and the significant inputs",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "acquisition-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "bf67a08bc7fc91fc83f24c6dc24f5a3c3a7fa56e2dbe95116f15d62c9291efcc",
    "reader_sha256": "1f981a5a71612e0aa123425e32d8787398f39905857a88471cd2e080b7d2f9df",
    "title": "Acquisitions: map the transaction before allocating price",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "consolidation-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "ad72436c2ad5d0a3f02db8c78a0f6a7cd3ff11d3f14c57186251ac258cf7aa86",
    "reader_sha256": "79ac6cd1f99ed90d8475999d69c4abee014ea3df2ff80695445e835d3c702803",
    "title": "Consolidation: connect control rights to evidence",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "income-tax-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "7346c3474c5b5806790f7f0d751538e6473613cb4c0a4c30fc6af381d97316ca",
    "reader_sha256": "f57e3e94e09a99fcf9424b38bd93c071624b293886e872ad3ad36c46e4e7c220",
    "title": "Income taxes: reconcile the provision without mixing tax regimes",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "foreign-currency-workbook": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "2de7c3a87e7d672d4c93aad8d6ec9cc7e44fe29a957040ef17a4518b9d6d3b34",
    "reader_sha256": "3901b76aacdc835d6064cb61ed1c60c7be17df1fcc6dccfbbf8a805ea217b211",
    "title": "Foreign currency: separate measurement, translation, and rate policy",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "going-concern-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "d82fafd7d78a646dcb8ea1a0a0385a0883ed36ac078f0ed2e6a6a689b4a95a8e",
    "reader_sha256": "493d03374db0ec8e7347c70a3cd07bbb8945fa5d28d3fc1c1cdf25b3fa0b5d8f",
    "title": "Going concern: separate management assessment from audit work",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "subsequent-events-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "8723d13b7789f5697833505f797b454fc315a4ee2d3b5247987f0169585c2942",
    "reader_sha256": "0bfd55008e831ca70c6999b743386f01f0b86afa4793911dc0b9f44d1cbc7e3c",
    "title": "Subsequent events: build a chronology, not a keyword label",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "related-party-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "932f4477ef39c9776b538b442f8dabe06965336d9db20109dc08f8f5163a863d",
    "reader_sha256": "9405c3a895ce5a5e8525d2a5994f54a8e21882aa1108ac0f5ac8b3ffcd008e66",
    "title": "Related parties: connect relationships, transactions, and disclosures",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "software-cost-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "2e5edadea588c1fb77576d7fac540a28cb1112a1adb3ba6b7feb1cbb4fc98921",
    "reader_sha256": "eabbee6674595cb07f7ca15ff92d4626def796406801ab6313178cec120484f1",
    "title": "Software costs: organize the project facts before choosing a model",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "debt-workbook": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "77288c98b4170e278558941724bb3c9ff35285d5bfc62845dbeef7da8cd99ed4",
    "reader_sha256": "fda2af25b6893a8c1c982669e3f744275f65a163179059e776ce6a679bf6505d",
    "title": "Debt and equity-linked instruments: read the complete terms",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-cash-flow-bridge": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "5589d5dc04ddbb6e9424080a583a9d4af758164ce8dc43d5c8a47d0747fa4959",
    "reader_sha256": "97f60f108ad6b093f5401998f6b0375d70164c001109c3f66903075b1d9def6f",
    "title": "Worked case: a balance-sheet movement is not a cash-flow line",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-fx-payable": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "2a7a24b9a3529619620be8cd3ed356e3963fdf958e7bfbaecf6b251e786a2d6a",
    "reader_sha256": "4c23c8f98fa82908791e6624d9f5ab4963b4b06f3cd534d89568c19d887f6732",
    "title": "Worked case: an explicitly assumed foreign-currency payable",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-liquidity-timing": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "6ac33ff39832ad4f67b848593c6732b61f634ecef90c93c799a6521e38a5f017",
    "reader_sha256": "c104bbb81ef7ea014ee090aed25f2dffcca74ffdd6d1aa7ec72a9d17de3007c0",
    "title": "Worked case: positive ending cash can conceal a funding gap",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "estimate-register-template": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "b940eb5c0a1e1bedce748e4eacc83273945f2780da38214e08a67b8e923c4bcd",
    "reader_sha256": "11c30a50de12784739c67513f1a3bb47e061cc262dbd31fa50505eb944796430",
    "title": "Template: accounting estimate and sensitivity register",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "subsequent-event-register-template": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "d368f9e3d86443929ca69f41c48b9b88260d75112664043a46592f08f57c0437",
    "reader_sha256": "b2d3d76f7e663d33ccb092bb8a396b56ff10202d186ed585c16942cc28cba43e",
    "title": "Template: subsequent-event chronology",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "currency-policy-template": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "be3e53a1fa35bd5528dc775a062d30549c915a66ed1311bd002f9c5998671e73",
    "reader_sha256": "f5037fd32138f80c921fe88683eac28cc6acd2cb69fb222e358c34db63fb306c",
    "title": "Template: currency and exchange-rate policy evidence",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "research-study-questions-v06": {
    "canonical_version": "1.1.0",
    "canonical_sha256": "83938424b2691f15e32c9570a4645a20ce71c6951ac562ecf26be51ee575b869",
    "reader_sha256": "ee12f28c9c41c57f1ed53c9c3f4dc424eecba3fcfa77c15a042c7a9d55a70575",
    "title": "Expanded study questions: evidence and model selection",
    "creator_credit": "Open Source Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "itgc-evidence-workbook": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "8a4693fdf81c76ff48a70671fbbe87009aa1c8c5ebdeaf0aeb14ec58bab3261b",
    "reader_sha256": "97b5dcfad23703301c8303955807f880caf127c227dfc1aeaad674dd0b005950",
    "title": "IT control evidence: six worked cases and a review template",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "federal-igt-reconciliation": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "4831425f410b136125cbf7813a43fadc9f1935d34d992409633157a63e91c812",
    "reader_sha256": "82fe1c7310dca0fbfa8b16205f2ac5f74948c12c55c773a7203cb37db1fcaecd",
    "title": "Federal interentity reconciliation: explain differences before proposing corrections",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "federal-mda-evidence": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "8e85e23fd7d96f4a5c5169e9b5522b0678c41e21d2424e2388c3019469c82ccc",
    "reader_sha256": "12b2ee0d445971cfa9ea16a078776b9f75c6322d453af48485ed0abaf0d5d90c",
    "title": "Federal MD&A evidence workpaper: connect costs, results and uncertainty",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "audit-proxy-measurement": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "2c94f2712d4edf2b7f797d0e5ac3355dcc6e25d5a0b0709af89b2a4cd732c11f",
    "reader_sha256": "0f1be3a2ab37070a20d39051142b1b8dc23d947a6e5fe904dea8c7bf5974d85f",
    "title": "Equal audit scores, different evidence: inspect the measure before the conclusion",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "recovery-reconciliation": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "9bed04435d557f2b4a4b6c55d1fddad391c240a282604cf21610e931350bb6d8",
    "reader_sha256": "ab15f25dd2aa77e016506b0e820f99a4b67ecf0c04f83303ed27aede0666273d",
    "title": "Recovery evidence workpaper: reconcile files, transactions and service readiness",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "federal-budget-cost-bridge": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "5c3eef6a4fe0ca7086b3978ea01237f196db01acca10f600e75eec4302699c52",
    "reader_sha256": "41be1064c3b12a430837d451c3eec6164bb9e12cbc1cf1c5ed7b791c347728cd",
    "title": "Federal accounting evidence workbook: budget authority, obligations, payments and accrued costs",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "government-audit-evidence": {
    "canonical_version": "2.0.0",
    "canonical_sha256": "862a19213aa05cde116abcd61f20570846b1e2547610bbdea0a8127df71141dc",
    "reader_sha256": "db0d6d7fa29a274d019c04dc144e113aaf323e4cfa3383a3d7b240ad3ed84405",
    "title": "Government-audit evidence case: two engagements, three clocks and an unresolved edition",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "esg-evidence-boundaries": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "4077149d6d53fc669253ccd8e271cadd1ced0ce284f7ee76e82747f3f1771128",
    "reader_sha256": "ce5042b2e96b78f43dc877711e9e1a68ba3ed43dd699a3e7585b12065613791d",
    "title": "ESG evidence: define the claim before choosing a metric",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-esg-units-and-boundary": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "9adf1f2efda555e800f57aa4cb86217776bcdc89a91474b8f70c175414f95297",
    "reader_sha256": "38c13c299d05883b9849408574227832d7f83a3e812b1762cf1f5e5e439bdfed",
    "title": "Worked case: units, duplicate meters and an intensity claim",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "esg-evidence-worksheet": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "af82bb9211b952fabdc09acccd11ffeb3810c09ba089de68e0268c60be10a1e7",
    "reader_sha256": "23566823ec04f84ecce066f60d2ed1337dbe2b5f59e761d050828e81e347f2e0",
    "title": "ESG claim and evidence worksheet",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "ferc-research-and-reconciliation": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "027a170684a558b756bab341ae673a97b9347cd30cc7904fc2e9b18e158b14a2",
    "reader_sha256": "a4bb2a6e379d7ee986cdc29c6942253b46493a216567f73bcd76cac73915cd67",
    "title": "FERC research: connect the ledger, authority and reporting destination",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "case-ferc-reconciliation-gaps": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "e4096fa98cfe9d411cc66da9d23146b4071bf78effe431f38c5f50703ce5a0a7",
    "reader_sha256": "c53de78cef370aeb94f166555e44a0356d4f2d9efa91ce3738e1e1097b24863a",
    "title": "Worked case: a balanced bridge can still contain unresolved mappings",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "ferc-mapping-evidence-template": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "0e427011c11c2f1527714978340c5aa5add18fd315486ac3702dee8b1d9344ca",
    "reader_sha256": "5eca64d0705b04c2e6264a988787fd92ebb58c0fc05ff9fbae284835b7feaaeb",
    "title": "FERC ledger-to-report evidence worksheet",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "sec-mda-controls-map": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "49d30eca518214b861200e7c7f5036b4861c4a9c63cab9f1c44769be6f831fb1",
    "reader_sha256": "320ecd7be94ce36a52086e8c9dd5015f14e2876c6da75d9476b5ec258b3d2fab",
    "title": "SEC MD&A and controls: a dated map of different reporting questions",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "sec-nongaap-communication-scope": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "ecef494f822d2226170591759c0d17d10cd23ff058b98efc7bff90a369972d3a",
    "reader_sha256": "3efbc5d9f37b7b59ef7b66570f42071709f04730e3766b84a0db9223db9b1d4a",
    "title": "Non-GAAP communication scope: connect Regulation G, Item 10(e) and Form 8-K",
    "creator_credit": "Open Accounting contributors",
    "license": "CC-BY-4.0"
  },
  "fasb-credit-loss-pools": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "946d4bcbd529001e4391b5db3ce4b4d0d3a9febc7282d962641bc5bfb7f51cb9",
    "reader_sha256": "b8f564ba0d67e635bd80a66ec3a59790fac39029dce36de0d76e597e7b1621e5",
    "title": "Expected credit losses: build a pooled estimate and explain its movement",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-loan-fee-yield": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "cb02e659aa63e62f7fb0648a1c74b177ee08ad74709e8991952c73c392834517",
    "reader_sha256": "495e19c7a71f74f10817e47a4376a86644ae41ffde915e098ee6a0e6313b7394",
    "title": "Loan origination fees: distinguish cash collected from interest earned",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-deferred-tax-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "f6102358c26b51f196e6bfae848ea066c6ef86ebe0402a6d52bd42de8f52e67c",
    "reader_sha256": "141394a2cc2acf28df4c4ff25bce26ad840f213f6fc1ad648ee2ff182bcd691d",
    "title": "Deferred tax assets: connect a future deduction to a realizability assessment",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-sale-recognition-control": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "a6d8cf53df2bc7c57d166ff2d937ac6d3f2c28492615e21334e5f0e38acd5daf",
    "reader_sha256": "4333c484808a2f0d8f5776e77c4502954f9b23526e2be7d5a49912957616c106",
    "title": "Selling a nonfinancial asset: separate the bank deposit from the accounting sale",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-fund-governmentwide-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "a49c8792e7c722e0a5293ca07acd7deef615cf70d02baa4fcff3577e7c2a5c1f",
    "reader_sha256": "29776627bc2cc4918f0b504826f4b2d5ec4647a2c606de1a1b3339d15566dd9e",
    "title": "Governmental funds and government-wide reporting: one purchase, two perspectives",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-fund-balance-constraints": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "a362648d358861e2965afb28678616749cf00178f93a6d6c88cde04bbb280fff",
    "reader_sha256": "4680dbf699a5358e3bca3ba4e847a08def682bab7240a06cba5cfbd70e84ab31",
    "title": "Fund balance: identify the constraint before calling money available",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-lease-two-statements": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "b6f66c1d616cb17835476fbda664cf3d8230d5b1e28dbe68b9b62bb8dd7cf052",
    "reader_sha256": "ab4702f653933f67f9ad5654977151093d6026fb0302338fdced7dfe3e718efe",
    "title": "Government leases: follow one payment through the liability and the fund",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-sbita-implementation-costs": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "4f923ca86647a91d5c930a754f7d4805c99dc5dcd644cf9f45123cbc0edb9cd6",
    "reader_sha256": "f9c8a240785ebae7ed1694711da716f9e9284d85f0540d3d21b59fc9238ed2f5",
    "title": "Government software subscriptions: classify the work, not the invoice label",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "aicpa-service-assurance-choice": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "a22d85578337fc3d2deeeb31a0ec3c05eba65331be0767714fa8060e56c62902",
    "reader_sha256": "b3fe4640d3a71d398d06d7a9494ab6dea1eba33d24cb0cd3f3ae2d1373e25135",
    "title": "Audit, review, compilation and preparation: begin with the report the user needs",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "aicpa-assertion-direction": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "0cc7ced156a4cf5e6b0dc0135228c6a740f1b8168844b96f095ee9d4c2019f5e",
    "reader_sha256": "3e08f699743103bd33109840eaeea9a4cf9a7b44e17e019a7641059bf1eb590d",
    "title": "Audit assertions: the direction of a test changes what it can show",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "aicpa-payroll-analytics": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "ac32ac7c21263f7bfc32d7da36619a8c05be2be44de4727db8c46f61f9750909",
    "reader_sha256": "11f881a6841098e378cd13f840d86a95bd2e84bd0ef66fd155331d3bda78aa9d",
    "title": "Analytical procedures: make an expectation that can actually be challenged",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "aicpa-selection-versus-sampling": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "36614e4e1e3147f55071699fca78a736afc63e62c7b692a4f17f2a69634e8efc",
    "reader_sha256": "6f1b96eee8607ebdb9f41b266cb8e0c4900cdc27960c5d880dae5ed2fee314fb",
    "title": "Selected items and audit samples: 60% coverage is not a population conclusion",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-grant-eligibility-cash": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "8ea0b4ddea7531cb61efa3e8a300f75dc12b84baa4943526ff120e572d1b2adf",
    "reader_sha256": "b8b4c91dbdbed7b2e706ab47b97bc1f3bc6d84790555c89e2336b26bfe0db424",
    "title": "Government grants: separate eligibility, timing and cash",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-compensated-absence-liability": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "7e05cbde140c89a706ec6f1079a26bdbccb7650de808f796e62ad0bab90a7528",
    "reader_sha256": "40c76be103eb48de8f625cc7a38a6165cb91fff376a7d3389d0fd14c7cf5524c",
    "title": "Compensated absences: measure earned leave at the reporting date",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-capital-asset-exit-donation": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "ada473734d2d4ebf9d464140014dfdf60f9c65ef9e5f869fa4092003900cd4e7",
    "reader_sha256": "908a0a33ade766ecbc4c52656707a88338a5c5c8c012a16c5d361e3e0637b883",
    "title": "Government capital assets: reconcile disposals, proceeds and donations",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-estimate-error-periods": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "7957cb6f2bbce6dac16af7d4d477864732618a1fef68caa60b81cbf9897465bc",
    "reader_sha256": "759d32c6c4f1d157f769ce1d178e25d1fc884cbc4ab9b3f1c99bf648bf6b5930",
    "title": "New estimate or old error: identify which reporting periods change",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-interfund-loan-transfer-reimbursement": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "8b4536ff9c50afea7bf0894539196a02ba229393483340142f592aebe3189e8d",
    "reader_sha256": "52fe7981e9215a146a1456d74b35a0ace6cbbb7c4c6b748488acc5fff797ba8f",
    "title": "Interfund funding: distinguish loans, transfers and reimbursements",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-pension-expense-contribution": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "68dc6454da94318fc3fb0410aa7ad5908e16e44adefc6c8d155ed2a37a6f5f2b",
    "reader_sha256": "bc822a5083a5a417be13c6ef5b9199ad06569ed8426ae39b8d29c57f65c8b0b3",
    "title": "Government pensions: reconcile expense, contributions and measurement dates",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-securities-measurement-oci": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "a1df48970f60ca5211ec122de4207d088ae15e75a26ead064abb9d16624bac13",
    "reader_sha256": "b662204530fc7ddfd80bb423fd6bffcc0e2e39c6958f6933e65e7f7d7c3deba9",
    "title": "Debt securities: separate market movement from amortized cost and credit loss",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-bond-premium-yield": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "688ea9919f9b41cb8c4e2f662573be4045782f10d302cce3314e5ab32d253671",
    "reader_sha256": "8c3ca9788abfe22942aac36e3f8d5d30716864744e884b1532847ab1ef7fcf67",
    "title": "Purchased bond premiums: reconcile coupon cash with effective interest",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-equity-method-income-distributions": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "68407ce781c636f2f016fdfb9275a6f39ffa89db131dbd04dcdc7f6e10cb7ab4",
    "reader_sha256": "2ebf915551a17209567304035d13a734d3d8fa3c08f263050a82c982bc0f689a",
    "title": "Equity-method investments: income and cash distributions move different balances",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-debt-replacement-test": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "11743d55d23a39f38eff40f2dd32943ad171a4be98a8c5b75b29bd6ff524c112",
    "reader_sha256": "b13d861111640c93bc084b29057284d4ad050f612b0057a390d6a0a8d642c701",
    "title": "Debt replacement: compare revised cash flows before choosing a gain or loss",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-private-grant-conditions": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "0962435c4df4f7c86fb6a791b0eb39d4f75f7c23b4a1a9f964ce816c657c7f40",
    "reader_sha256": "eb9d20bcd4669a62e68584d20300c4c39ca521a2286e0867b14517d96b6e4984",
    "title": "Private grants received by banks: separate the receipt date from the recognition condition",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-operating-cash-direct-indirect": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "56cd7c425b3331a93fffa7519a320b504c989c3880d8204aae1bd7f4dde6ea72",
    "reader_sha256": "6dc1049203689be20c3735e5cb226fccc37c3798d2140aca853adf0e131258e0",
    "title": "Operating cash flow: reconcile gross cash receipts with the indirect bridge",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-custodial-resource-flows": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "4584a2b69a2588fbb211d3529dd5261c07ea46b494f4b9bf5e63d35162b5ca5d",
    "reader_sha256": "26283fd7bd61d95c93e4195a3695fe12012b769565f15a0197fdc3f4f1117c47",
    "title": "Custodial funds: reconcile money held for other beneficiaries",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-cash-defeasance-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "081db42181f7c7d33a95947fb885e20d7a61ecb869edb09dbadaa443f9c711ed",
    "reader_sha256": "d1744c7cec0433746e1e08dac8a44ba3d29a367f550787148dce38caf308e6bf",
    "title": "Existing-resource debt defeasance: separate the fund payment from the liability exit",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-aro-current-value-rollforward": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "c98ab89f5b9dd81dbb2c9bed3a41b3418cbcfcc18c30c82f045de67be98b7077",
    "reader_sha256": "fe5273153fd2832712c7d5126934dbfa94cdc8fe67a03754c28112744ddbdd6a",
    "title": "Asset retirement obligations: connect current outlays with deferred-resource expense",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-oreo-holding-register": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "0562384c5f381c88bdaf1d5dc9ecf0953d9ad3ad0bac5dededcdc9142fc7c3b1",
    "reader_sha256": "43deaf543aa72dca099726dd22550bfc14b6e67fee824beee939ee9e87ccf67e",
    "title": "Foreclosed property held for sale: reconcile carrying value and holding activity",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-goodwill-test-order": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "ee8855475d18a5d50d2b6822cf52a89966f02bfc3da23567d577f57d94cfc4ed",
    "reader_sha256": "67bfbd81c8d525f4f0e91e06311b068f61232ad9f3cd6b57061f8bf661c83f5b",
    "title": "Goodwill testing: sequence other asset losses before applying the goodwill cap",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "aicpa-aup-examination-choice": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "bcb83a8aa716a18dc9b6f4d039f3e12cc61bcde25f6333cbe65f7f9bb7e0ae46",
    "reader_sha256": "b67486fea03f79c53d46fe24e7e2bf4b5ac5b23129cf36fe77226d850f9a9d8e",
    "title": "Agreed-upon procedures and examinations: match the report to the user’s question",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "irs-crypto-receipt-control": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "89ecd313b411398bfc49f96e20f5126702b91feee357f7240c359971c3e7db9f",
    "reader_sha256": "1646981a1ea47e1b39f72e5363b79e9d2602f8a1fae40cbfb772755bfc2d4cb3",
    "title": "Cryptocurrency hard forks: distinguish a ledger event from receipt and control",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "irs-replacement-check-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "c0d6ab675bbdf3a3fa1beb6bf9c0830b67a6358e5bd696f7c2a2bf882daad120",
    "reader_sha256": "43f3d6adecfdccf9d29058e2a3dfff70aa4803abeb3611eac1ae19d3da73a4c9",
    "title": "Replacement retirement checks: reconcile prior withholding before treating cash as new income",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "irs-medicaid-rebate-gross-receipts": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "3837ae892a1344c5d3ac0f07a477f74fa6655798d353b1a29e4bda87bdd429bb",
    "reader_sha256": "1ba2460e932946c37b56aad002ccdade573db2337b00de0e7a44073256407edb",
    "title": "Medicaid rebates: trace the price adjustment through a tax gross-receipts bridge",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "irs-ppp-obsolescence-timeline": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "55342d489af7fa36f19b7fbbde06bee510da2618651f5e37a5d6aea7d7abc44e",
    "reader_sha256": "45b8335e3dde2790abfac43fbd1c4323ddd79912e2d9a894c8042d1390ebda6d",
    "title": "PPP expense research: replace an obsolete conclusion without erasing the evidence trail",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-mortgage-commitment-register": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "7c66df1851fc0d3032a07ee6e563300d3df64cb7cee3f81c7bbab8b12133a0a5",
    "reader_sha256": "6242e590dc684b0646e874f13bd75362df664e5186d7c62c5637836ff59ccd4a",
    "title": "Mortgage commitments: separate notional, fair value and earnings",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-servicing-measurement-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "c0ea3de245fa0a5b11b32397c9902d4459b0471e4f80c79600aa3c6763d7cce3",
    "reader_sha256": "a3ef200fa5e60d910ba5f6835d3111d44433d745769a79a473d5ed335aa4986e",
    "title": "Servicing assets: keep the measurement election separate from cash collected",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-impairment-insurance-timing": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "a702178f4a550c362021b028f5d6ea03b8594ca63fffd496b5c0650eaf7227ec",
    "reader_sha256": "aa6820cfe446c51fd1b551ddec0f79709f4bbd376bdbb84cb9bfa05496caa4fd",
    "title": "Capital impairment and insurance: separate the asset loss from the recovery timeline",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "gasb-opeb-nontrust-rollforward": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "68e026cc32d6c0026328a71f3f00e9db747f0cbf36f11d55ac4ce0eb78c8251d",
    "reader_sha256": "69f94cf7bcb6646f3ccd4bfc054d3896360773ce33c59489a9c95a34571d9e9f",
    "title": "Nontrust OPEB: reconcile the liability, deferred resources and benefit payments",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-mutual-fund-sale-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "fa1e773e6b6664511c64f4ae0c12021be83bd6c2e3db2bda6605d109245d6c8a",
    "reader_sha256": "35a9e80be7c558910c5bd520b1887dec3c056588017d35ff779310314a5e867d",
    "title": "Mutual funds: reconcile periodic marks and a partial sale",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-unfunded-commitment-liability": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "555e33f783c442b96869c80ae8042bacbb7bf2ab6340e8b362f8495a2dd937b2",
    "reader_sha256": "9e6d54e22d9aee2780b506d894ac584958fa2dfbdb4c39dc0686a3470358ed89",
    "title": "Unfunded commitments: connect expected draws to a separate loss liability",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-boli-premium-cash-value": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "2314a7c9cba0edf993975c150dc158d6051042ffce6eeb72ae72a31eebb4efd6",
    "reader_sha256": "92dc2e72a482f8feda81dc112c8a99dae077a4117cd757fcd0f17894608836fd",
    "title": "Bank-owned life insurance: reconcile premiums, cash value and period income",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-startup-cost-close": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "b54bfdb5f05787ba06a54a2a8934d7ff01d89cad24658dc8c8fa5909b8319ca3",
    "reader_sha256": "50171ff01199ca32ceb3be1cfb565f996264cf841fef6a0695ddb6ae25c32c31",
    "title": "Startup costs: separate launch spending from the equipment rollforward",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-loan-sale-classification-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "327e18d7aae0d0558c77fa5e6e74afb2c60b9e9a013828ae0877ff8dd298fd0b",
    "reader_sha256": "910e8d3d1a64d22ad338b3e74283f187889594a34781fe6f48e0e9fe1f4ac9f8",
    "title": "Loan sale plans: reconcile the credit allowance and the held-for-sale valuation account",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-loss-range-accrual-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "a7821e10c0974cb17dbd69343bfb0f372dadce987ba580f6026ec9ff69877f88",
    "reader_sha256": "150372f30d1ad20efe5e211dcebb42f22c51919e0e0ec388edefb5a41da18017",
    "title": "Loss contingencies: turn supported estimates into a liability rollforward",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-equipment-useful-life-reset": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "5184d5c4abfd326385dc6dc5079a88d67ee4f36f980979c27b5ff4e72a165b7a",
    "reader_sha256": "459061f4194645d4953f1681a84e7e37e479d21bd331533669fd9ec9b5b0ccc8",
    "title": "Equipment retirement plans: rebuild depreciation from the remaining service period",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  },
  "fasb-stock-offering-cost-bridge": {
    "canonical_version": "1.0.0",
    "canonical_sha256": "ac373a8dcf593410440b930f50554ce56ee178ed22ed837b3f80284abd1ddf6e",
    "reader_sha256": "6cf0b30002042251fb32e4fc6ce4790388749e2345be55dd993346c6c292721d",
    "title": "Equity offering costs: reconcile cash, paid-in capital and an abandoned attempt",
    "creator_credit": "Open Source Accounting contributors",
    "license": "LicenseRef-Ray-Sang-Noncommercial-NoAI-1.0"
  }
};
