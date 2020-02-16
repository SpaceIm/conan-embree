import glob
import os

from conans import ConanFile, CMake, tools

class EmbreeConan(ConanFile):
    name = "embree"
    description = "Intel's collection of high-performance ray tracing kernels."
    license = "Apache-2.0"
    topics = ("conan", "embree", "raytracing", "rendering")
    homepage = "https://embree.github.io/"
    url = "https://github.com/conan-io/conan-center-index"
    requires = "tbb/2019_u9"
    exports_sources = "CMakeLists.txt"
    generators = "cmake", "cmake_find_package"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "backface_culling": [True, False],
        "ignore_invalid_rays": [True, False],
        "ray_masking": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "backface_culling": False,
        "ignore_invalid_rays": False,
        "ray_masking": False
    }

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def build(self):
        os.remove(os.path.join(self._source_subfolder, "common", "cmake", "FindTBB.cmake"))
        cmake = self._configure_cmake()
        cmake.build()

    def _configure_cmake(self):
        if self._cmake:
            self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["EMBREE_STATIC_LIB"] = not self.options.shared
        self._cmake.definitions["BUILD_TESTING"] = False
        self._cmake.definitions["EMBREE_TUTORIALS"] = False
        self._cmake.definitions["EMBREE_GEOMETRY_CURVE"] = True
        self._cmake.definitions["EMBREE_GEOMETRY_GRID"] = True
        self._cmake.definitions["EMBREE_GEOMETRY_INSTANCE"] = True
        self._cmake.definitions["EMBREE_GEOMETRY_QUAD"] = True
        self._cmake.definitions["EMBREE_GEOMETRY_SUBDIVISION"] = True
        self._cmake.definitions["EMBREE_GEOMETRY_TRIANGLE"] = True
        self._cmake.definitions["EMBREE_GEOMETRY_USER"] = True
        self._cmake.definitions["EMBREE_RAY_PACKETS"] = True
        self._cmake.definitions["EMBREE_RAY_MASK"] = self.options.ray_masking
        self._cmake.definitions["EMBREE_BACKFACE_CULLING"] = self.options.backface_culling
        self._cmake.definitions["EMBREE_IGNORE_INVALID_RAYS"] = self.options.ignore_invalid_rays
        self._cmake.definitions["EMBREE_ISPC_SUPPORT"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("LICENSE.txt", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "share"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "uninstall.command"))
        for cmake_file in glob.glob(os.path.join(self.package_folder, "*.cmake")):
            os.remove(cmake_file)

    def package_info(self):
        self.cpp_info.libs = self._get_cpp_info_ordered_libs()
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(["dl", "m", "pthread"])

    def _get_cpp_info_ordered_libs(self):
        gen_libs = tools.collect_libs(self)

        lib_list = ["embree3", "embree3_sse42", "embree3_avx", "embree3_avx2", \
                    "embree3_avx512knl", "embree3_avx512skx", "simd", \
                    "lexers", "tasking", "sys", "math"]

        # List of lists, so if more than one matches the lib both will be added
        # to the list
        ordered_libs = [[] for _ in range(len(lib_list))]

        # The order is important, reorder following the lib_list order
        missing_order_info = []
        for real_lib_name in gen_libs:
            for pos, alib in enumerate(lib_list):
                if os.path.splitext(real_lib_name)[0].split("-")[0].endswith(alib):
                    ordered_libs[pos].append(real_lib_name)
                    break
            else:
                missing_order_info.append(real_lib_name)

        # Flat the list
        return [item for sublist in ordered_libs for item in sublist if sublist] + missing_order_info
