/* SPDX-License-Identifier: MIT
 * Supply metadata to .NET without replacing Wine's WinRT activation factories.
 * The metadata comes from microsoft/windows-rs; this does not implement WinRT APIs.
 */
#include <windows.h>
#include <objbase.h>
#include <winstring.h>
#include <wchar.h>

HRESULT WINAPI RoResolveNamespace(HSTRING name, HSTRING metadata_dir,
    DWORD graph_count, const HSTRING *graph_dirs, DWORD *file_count,
    HSTRING **files, DWORD *namespace_count, HSTRING **namespaces)
{
    static const WCHAR path[] = L"C:\\windows\\system32\\WinMetadata\\Windows.winmd";
    const WCHAR *namespace_name;
    HSTRING *result;
    HRESULT status;
    (void)metadata_dir;
    (void)graph_count;
    (void)graph_dirs;
    if (file_count) *file_count = 0;
    if (files) *files = NULL;
    if (namespace_count) *namespace_count = 0;
    if (namespaces) *namespaces = NULL;
    if ((!file_count || !files) && (!namespace_count || !namespaces)) return E_INVALIDARG;
    namespace_name = WindowsGetStringRawBuffer(name, NULL);
    if (!namespace_name || wcsncmp(namespace_name, L"Windows.", 8)) return HRESULT_FROM_WIN32(ERROR_NOT_FOUND);
    if (!file_count || !files) return S_OK;
    if (GetFileAttributesW(path) == INVALID_FILE_ATTRIBUTES) return HRESULT_FROM_WIN32(ERROR_FILE_NOT_FOUND);
    result = CoTaskMemAlloc(sizeof(*result));
    if (!result) return E_OUTOFMEMORY;
    status = WindowsCreateString(path, (sizeof(path) / sizeof(path[0])) - 1, result);
    if (FAILED(status)) { CoTaskMemFree(result); return status; }
    *files = result;
    *file_count = 1;
    return S_OK;
}
