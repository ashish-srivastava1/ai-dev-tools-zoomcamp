#!/usr/bin/env bash
# Deploy (create/update) or tear down the TableTurn CloudFormation stack.
#
# Usage:
#   POSTGRES_PASSWORD=... ./deploy.sh up          # create or update the stack
#   ./deploy.sh outputs                            # show stack outputs (URL, IP, ...)
#   ./deploy.sh down                               # delete the stack (removes all resources)
#
# Optional env vars: STACK_NAME (default tableturn), AWS_REGION (default us-east-1),
# DOMAIN_NAME, KEY_NAME, GIT_REF, INSTANCE_TYPE.
set -euo pipefail

STACK_NAME="${STACK_NAME:-tableturn}"
REGION="${AWS_REGION:-us-east-1}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$HERE/tableturn-stack.yaml"

cmd="${1:-up}"

case "$cmd" in
  up)
    : "${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD (min 8 chars, no quotes/spaces)}"
    aws cloudformation deploy \
      --stack-name "$STACK_NAME" \
      --template-file "$TEMPLATE" \
      --region "$REGION" \
      --capabilities CAPABILITY_IAM \
      --parameter-overrides \
        PostgresPassword="$POSTGRES_PASSWORD" \
        DomainName="${DOMAIN_NAME:-}" \
        KeyName="${KEY_NAME:-}" \
        GitRef="${GIT_REF:-main}" \
        InstanceType="${INSTANCE_TYPE:-t3.small}"
    echo
    echo "Deployed. Outputs:"
    "$0" outputs
    ;;

  outputs)
    aws cloudformation describe-stacks \
      --stack-name "$STACK_NAME" --region "$REGION" \
      --query 'Stacks[0].Outputs[].{Key:OutputKey,Value:OutputValue}' \
      --output table
    ;;

  down)
    aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"
    echo "Deleting stack '$STACK_NAME'... waiting for completion."
    aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"
    echo "Stack deleted."
    ;;

  *)
    echo "Unknown command: $cmd (expected: up | outputs | down)" >&2
    exit 2
    ;;
esac
