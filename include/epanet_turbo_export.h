#ifndef EPANET_TURBO_EXPORT_H
#define EPANET_TURBO_EXPORT_H

#if defined(_WIN32) || defined(__CYGWIN__)
#ifdef EPANET_EXPORTS
#define EPNT_API __declspec(dllexport)
#else
#define EPNT_API __declspec(dllimport)
#endif
#else
#if __GNUC__ >= 4
#define EPNT_API __attribute__((visibility("default")))
#else
#define EPNT_API
#endif
#endif

#endif // EPANET_TURBO_EXPORT_H
