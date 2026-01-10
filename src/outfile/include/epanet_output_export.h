
#ifndef EXPORT_OUT_API_H
#define EXPORT_OUT_API_H

#ifdef SHARED_EXPORTS_BUILT_AS_STATIC
#  define EXPORT_OUT_API
#  define EPANET_OUTPUT_NO_EXPORT
#else
#  ifndef EXPORT_OUT_API
#    ifdef epanet_output_EXPORTS
        /* We are building this library */
#      define EXPORT_OUT_API __declspec(dllexport)
#    else
        /* We are using this library */
#      define EXPORT_OUT_API __declspec(dllimport)
#    endif
#  endif

#  ifndef EPANET_OUTPUT_NO_EXPORT
#    define EPANET_OUTPUT_NO_EXPORT 
#  endif
#endif

#ifndef EPANET_OUTPUT_DEPRECATED
#  define EPANET_OUTPUT_DEPRECATED __declspec(deprecated)
#endif

#ifndef EPANET_OUTPUT_DEPRECATED_EXPORT
#  define EPANET_OUTPUT_DEPRECATED_EXPORT EXPORT_OUT_API EPANET_OUTPUT_DEPRECATED
#endif

#ifndef EPANET_OUTPUT_DEPRECATED_NO_EXPORT
#  define EPANET_OUTPUT_DEPRECATED_NO_EXPORT EPANET_OUTPUT_NO_EXPORT EPANET_OUTPUT_DEPRECATED
#endif

/* NOLINTNEXTLINE(readability-avoid-unconditional-preprocessor-if) */
#if 0 /* DEFINE_NO_DEPRECATED */
#  ifndef EPANET_OUTPUT_NO_DEPRECATED
#    define EPANET_OUTPUT_NO_DEPRECATED
#  endif
#endif

#endif /* EXPORT_OUT_API_H */
