"""Wrapper to call Phabricator's Differential Conduit API."""
# =============================================================================
# CONTENTS
# -----------------------------------------------------------------------------
# phlcon_differential
#
# Public Classes:
#   ReviewStates
#   Action
#   MessageFields
#   ParseCommitMessageFail
#   ParseCommitMessageNoTestPlanFail
#   ParseCommitMessageUnknownReviewerFail
#   ParseCommitMessageUnknownFail
#   Error
#   UpdateClosedRevisionError
#   WriteDiffError
#   UnknownParseCommitMessageResponseError
#
# Public Functions:
#   create_raw_diff
#   parse_commit_message
#   parse_commit_message_errors
#   create_revision
#   query
#   get_revision_status
#   update_revision
#   create_comment
#   create_inline_comment
#   get_commit_message
#   close
#   create_empty_revision
#   update_revision_empty
#   get_revision_diff
#   get_diff
#   write_diff_files
#
# Public Assignments:
#   AUTHOR_ACTIONS
#   REVIEWER_ACTIONS
#   USER_ACTIONS
#   CreateRawDiffResponse
#   GetDiffIdResponse
#   ParseCommitMessageResponse
#   RevisionResponse
#   QueryResponse
#   GetDiffResponse
#
# -----------------------------------------------------------------------------
# (this contents block is generated, edits will be lost)
# =============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import phlsys_conduit
import phlsys_dictutil
import phlsys_namedtuple


# Enumerate the states that a Differential review can be in
# from ArcanistRevisionDifferentialStatus.php:
class ReviewStates(object):  # XXX: will derive from Enum in Python 3.4+
    needs_review = 0
    needs_revision = 1
    accepted = 2
    closed = 3
    abandoned = 4


# Enumerate the actions that can be performed on a Differential review
# from .../differential/constants/DifferentialAction.php:
class Action(object):  # XXX: will derive from Enum in Python 3.4+
    close = 'commit'
    comment = 'none'
    accept = 'accept'
    reject = 'reject'
    rethink = 'rethink'
    abandon = 'abandon'
    request = 'request_review'
    reclaim = 'reclaim'
    update = 'update'
    resign = 'resign'
    summarize = 'summarize'
    testplan = 'testplan'
    create = 'create'
    addreviewers = 'add_reviewers'
    addccs = 'add_ccs'
    claim = 'claim'
    reopen = 'reopen'


# Enumerate all the actions that an author may perform on a review
# map the strings that appear in the web UI to string that conduit expects
AUTHOR_ACTIONS = {
    "close": Action.close,
    "comment": Action.comment,
    "plan changes": Action.rethink,
    "abandon": Action.abandon,
    "request review": Action.request,
    "unabandon": Action.reclaim,
    "reopen": Action.reopen,
}

# Enumerate all the actions that an reviewer may perform on a review
# map the strings that appear in the web UI to string that conduit expects
# note that everyone except the author of a review is considered a reviewer
REVIEWER_ACTIONS = {
    "comment": Action.comment,
    "accept": Action.accept,
    "request changes": Action.reject,
    "resign as reviewer": Action.resign,
    "commandeer": Action.claim,
}

# Enumerate all the actions either a reviewer or author may perform
# map the strings that appear in the web UI to string that conduit expects
USER_ACTIONS = dict(AUTHOR_ACTIONS.items() + REVIEWER_ACTIONS.items())


# Enumerate some of the fields that Differential expects to be able fill out
# based on commit messages, these are accepted by create_revision and
# accept_revision
# from phabricator/.../...DefaultFieldSelector.php
class MessageFields(object):  # XXX: will derive from Enum in Python 3.4+
    title = "title"
    summary = "summary"
    test_plan = "testPlan"
    reviewer_phids = "reviewerPHIDs"
    cc_phids = "ccPHIDs"


CreateRawDiffResponse = phlsys_namedtuple.make_named_tuple(
    'CreateRawDiffResponse',
    required=['id', 'uri'],
    defaults={},
    ignored=[])


GetDiffIdResponse = phlsys_namedtuple.make_named_tuple(
    'phlcon_differential__GetDiffIdResponse',
    required=[
        'parent', 'properties', 'sourceControlSystem', 'sourceControlPath',
        'dateCreated', 'dateModified', 'lintStatus', 'bookmark', 'changes',
        'revisionID', 'sourceControlBaseRevision', 'branch',
        'projectName', 'unitStatus', 'creationMethod', 'id', 'description'],
    defaults={},
    ignored=[])


ParseCommitMessageResponse = phlsys_namedtuple.make_named_tuple(
    'phlcon_differential__ParseCommitMessageResponse',
    required=['fields', 'errors'],
    defaults={},
    ignored=[])


class ParseCommitMessageFail(object):
    pass


class ParseCommitMessageNoTestPlanFail(ParseCommitMessageFail):
    pass


class ParseCommitMessageUnknownReviewerFail(ParseCommitMessageFail):

    def __init__(self, user_list):
        super(ParseCommitMessageUnknownReviewerFail, self).__init__()
        self.user_list = user_list


class ParseCommitMessageUnknownFail(ParseCommitMessageFail):

    def __init__(self, message):
        super(ParseCommitMessageUnknownFail, self).__init__()
        self.message = message

    def __repr__(self):
        return 'ParseCommitMessageUnknownFail({})'.format(repr(self.message))


RevisionResponse = phlsys_namedtuple.make_named_tuple(
    'phlcon_differential__RevisionResponse',
    required=['revisionid', 'uri'],
    defaults={},
    ignored=[])


QueryResponse = phlsys_namedtuple.make_named_tuple(
    'phlcon_differential__QueryResponse',
    required=[
        'authorPHID', 'status', 'phid', 'testPlan', 'title', 'commits',
        'diffs', 'uri', 'ccs', 'dateCreated', 'lineCount', 'branch',
        'reviewers', 'id', 'statusName', 'hashes', 'summary', 'dateModified',
        'sourcePath', 'auxiliary'],
    defaults={},
    ignored=[])


GetDiffResponse = phlsys_namedtuple.make_named_tuple(
    'phlcon_differential__GetDiffResponse',
    required=['changes'],
    defaults={},
    ignored=[
        'properties', 'sourceControlPath', 'parent', 'lintStatus', 'bookmark',
        'projectName', 'revisionID', 'creationMethod', 'unitStatus',
        'sourceControlBaseRevision', 'branch', 'id', 'dateModified',
        'dateCreated', 'sourceControlSystem', 'description', 'authorEmail',
        'authorName'])


class Error(Exception):
    pass


class UpdateClosedRevisionError(Error):
    pass


class WriteDiffError(Error):
    pass


class UnknownParseCommitMessageResponseError(Error):
    pass


def create_raw_diff(conduit, diff):
    response = conduit("differential.createrawdiff", {"diff": diff})
    return CreateRawDiffResponse(**response)


def parse_commit_message(conduit, corpus, partial=None):
    d = {"corpus": corpus, "partial": partial}
    d = phlsys_dictutil.copy_dict_no_nones(d)
    p = ParseCommitMessageResponse(
        **conduit("differential.parsecommitmessage", d))

    if not isinstance(p.fields, dict):
        raise UnknownParseCommitMessageResponseError(
            "p.fields is not a dict: {}".format(p.fields))

    phlsys_dictutil.ensure_keys_default(
        p.fields, "", ["summary", "testPlan", "title"])
    phlsys_dictutil.ensure_keys_default(
        p.fields, [], ["reviewerPHIDs"])
    return p


def parse_commit_message_errors(error_message_list):

    test_plan_error = str(
        "Invalid or missing field 'Test Plan': "
        "You must provide a test plan.")

    reviewers_error = str(
        "Error parsing field 'Reviewers': "
        "Commit message references nonexistent users: ")

    result = []
    for error in error_message_list:
        if error == test_plan_error:
            result.append(
                ParseCommitMessageNoTestPlanFail())
        elif error.startswith(reviewers_error):
            users = error[len(reviewers_error):-1].split(', ')
            result.append(
                ParseCommitMessageUnknownReviewerFail(users))
        else:
            result.append(
                ParseCommitMessageUnknownFail(error))

    return result


def create_revision(conduit, diffId, fields):
    d = {"diffid": diffId, "fields": fields}
    return RevisionResponse(
        **conduit("differential.createrevision", d))


def query(
        conduit,
        ids=None):  # list(uint)
    # TODO: typechecking
    d = phlsys_dictutil.copy_dict_no_nones({'ids': ids})
    response = conduit("differential.query", d)
    query_response_list = []
    for r in response:
        phlsys_dictutil.ensure_keys(r, ["sourcePath", "auxiliary"])
        r["id"] = int(r["id"])
        r["status"] = int(r["status"])
        query_response_list.append(QueryResponse(**r))
    return query_response_list


def get_revision_status(conduit, id):
    return query(conduit, [int(id)])[0].status


def update_revision(conduit, id, diffid, fields, message):
    d = {
        "id": id, "diffid": diffid,
        "fields": fields, "message": message
    }

    try:
        response = conduit('differential.updaterevision', d)
    except phlsys_conduit.ConduitException as e:
        if e.error == 'ERR_CLOSED':
            raise UpdateClosedRevisionError()
        raise

    response['revisionid'] = int(response['revisionid'])
    return RevisionResponse(**response)


def create_comment(
        conduit,
        revisionId,
        message=None,
        action=None,
        silent=None,
        attach_inlines=None):
    d = {
        "revision_id": revisionId,
        "message": message,
        "action": action,
        "silent": silent
    }
    if attach_inlines:
        d['attach_inlines'] = attach_inlines
    d = phlsys_dictutil.copy_dict_no_nones(d)
    response = conduit('differential.createcomment', d)
    response['revisionid'] = int(response['revisionid'])
    return RevisionResponse(**response)


def create_inline_comment(
        conduit,
        revisionId,
        file_path,
        start_line,
        message,
        is_right_side=True,
        line_count=None):
    d = {
        "revisionID": revisionId,
        "filePath": file_path,
        "content": message,
        "lineNumber": start_line,
        "isNewFile": is_right_side,
        'lineLength': line_count,
    }

    d = phlsys_dictutil.copy_dict_no_nones(d)

    return conduit('differential.createinline', d)


def get_commit_message(conduit, revision_id):
    d = {"revision_id": revision_id}
    return conduit('differential.getcommitmessage', d)


def close(conduit, revisionId):
    conduit('differential.close', {"revisionID": revisionId})


def create_empty_revision(conduit):
    """Return the revision id of a newly created empty revision.

    :conduit: conduit to operate on
    :return: revision id

    """

    empty_diff = "diff --git a/ b/"
    diff_id = create_raw_diff(conduit, empty_diff).id
    fields = {
        "title": "empty revision",
        "testPlan": "UNTESTED",
    }

    # TODO: add support for reviewers and ccs
    # if reviewers:
    #     assert not isinstance(reviewers, types.StringTypes)
    #     fields["reviewers"] = reviewers
    # if ccs:
    #     assert not isinstance(ccs, types.StringTypes)
    #     fields["ccs"] = ccs

    revision = create_revision(conduit, diff_id, fields)

    return revision.revisionid


def update_revision_empty(conduit, revision_id):
    """Update the specified 'revision_id' with an empty diff.

    :conduit: conduit to operate on
    :revision_id: revision to update
    :return: None

    """

    empty_diff = "diff --git a/ b/"
    diff_id = create_raw_diff(conduit, empty_diff).id
    update_revision(conduit, revision_id, diff_id, [], 'update')


def get_revision_diff(conduit, revision_id):
    result = conduit('differential.getdiff', {'revision_id': revision_id})
    return GetDiffResponse(**result)


def get_diff(conduit, diff_id):
    result = conduit('differential.getdiff', {'diff_id': diff_id})
    return GetDiffResponse(**result)


def _write_hunks(hunk_list, base_path, extra_path, diff_prefix_ignore_char):

    # nothing to do if the extra path doesn't exist
    # may have been deleted or added in this diff
    if not extra_path or not hunk_list:
        return

    if len(hunk_list) > 1:
        raise WriteDiffError('partial file: {}'.format(extra_path))
    elif int(hunk_list[0]['newOffset']) != 1:
        raise WriteDiffError('partial file: {}'.format(extra_path))
    elif int(hunk_list[0]['oldOffset']) != 1:
        raise WriteDiffError('partial file: {}'.format(extra_path))

    if os.path.isabs(extra_path):
        raise WriteDiffError('refusing abs path: {}'.format(extra_path))

    path = os.path.join(base_path, extra_path)
    directory = os.path.dirname(path)

    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(path, 'w') as outfile:
            for hunk in hunk_list:
                for line in hunk["corpus"].splitlines():
                    if line.startswith(diff_prefix_ignore_char):
                        pass
                    else:
                        print(line[1:], file=outfile)
    except IOError as e:
        raise WriteDiffError(e)
    except UnicodeEncodeError as e:
        raise WriteDiffError(e)


def write_diff_files(diff_result, path):
    left_base_path = os.path.join(path, 'left')
    right_base_path = os.path.join(path, 'right')

    for change in diff_result.changes:
        hunks = change["hunks"]
        _write_hunks(hunks, left_base_path, change["oldPath"], '+')
        _write_hunks(hunks, right_base_path, change["currentPath"], '-')


# -----------------------------------------------------------------------------
# Copyright (C) 2013-2015 Bloomberg Finance L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------ END-OF-FILE ----------------------------------
