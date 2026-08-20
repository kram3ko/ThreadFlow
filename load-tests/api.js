import exec from "k6/execution";
import http from "k6/http";
import { check, sleep } from "k6";
import { SharedArray } from "k6/data";

const baseUrl = __ENV.BASE_URL || "http://nginx";
const captchaFile = __ENV.CAPTCHAS_FILE || "./data/captchas.example.json";
const captchas = new SharedArray("captcha credentials", () =>
  JSON.parse(__ENV.CAPTCHA_CREDENTIALS || open(captchaFile)),
);

export const options = {
  scenarios: {
    daily_visitors: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.DAILY_USERS || 100000),
      timeUnit: "24h",
      duration: __ENV.DURATION || "5m",
      preAllocatedVUs: Number(__ENV.PREALLOCATED_VUS || 25),
      maxVUs: Number(__ENV.MAX_VUS || 250),
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{endpoint:list}": ["p(95)<500"],
    "http_req_duration{endpoint:search}": ["p(95)<1000"],
    "http_req_duration{endpoint:graphql}": ["p(95)<750"],
  },
};

function guestAddress() {
  const iteration = exec.scenario.iterationInTest;
  return `10.${Math.floor(iteration / 65536) % 250}.${Math.floor(iteration / 256) % 256}.${iteration % 256}`;
}

export default function () {
  const headers = { "X-Forwarded-For": guestAddress() };
  const list = http.get(`${baseUrl}/api/comments?sort=date&direction=desc&depth=2`, {
    headers,
    tags: { endpoint: "list" },
  });
  check(list, { "comment list is available": (response) => response.status === 200 });

  const searchTarget =
    exec.scenario.iterationInTest % 2 === 0
      ? "q=comment%20999999"
      : "author=LoadUser00042";
  const search = http.get(`${baseUrl}/api/search?${searchTarget}&limit=20`, {
    headers,
    tags: { endpoint: "search" },
  });
  check(search, { "search is available": (response) => response.status === 200 });

  const graphqlQuery = encodeURIComponent(
    "{ rootComments(first: 25) { id author { name } replies { id } } }",
  );
  const graphql = http.get(`${baseUrl}/graphql?query=${graphqlQuery}`, {
    headers,
    tags: { endpoint: "graphql" },
  });
  check(graphql, { "GraphQL is available": (response) => response.status === 200 });

  const credential = captchas[exec.scenario.iterationInTest];
  if (credential) {
    const created = http.post(
      `${baseUrl}/api/comments`,
      JSON.stringify({
        username: `Guest${exec.scenario.iterationInTest}`,
        email: `guest${exec.scenario.iterationInTest}@example.test`,
        homepage: "",
        text: "A comment created by the k6 workload",
        captcha_id: credential.id,
        captcha_answer: credential.answer,
      }),
      {
        headers: { ...headers, "Content-Type": "application/json" },
        tags: { endpoint: "create" },
      },
    );
    check(created, { "comment is created": (response) => response.status === 201 });
  }
  sleep(0.2);
}
