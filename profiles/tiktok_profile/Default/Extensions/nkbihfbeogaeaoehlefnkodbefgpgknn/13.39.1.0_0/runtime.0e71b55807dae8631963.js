/*! SES sources included by LavaMoat. Do not optimize or minify. */
;
// ses@1.15.0
(functors => options => {
  'use strict';

  const {
    Map,
    Object,
    ReferenceError,
    Reflect,
    TypeError,
  } = globalThis;
  const {
    create,
    defineProperties,
    defineProperty,
    freeze,
    fromEntries,
    getOwnPropertyDescriptors,
    getOwnPropertyNames,
    keys,
  } = Object;
  const { get, set } = Reflect;

  const {
  } = options || {};



  const cell = (name, value = undefined) => {
    const observers = [];
    return freeze({
      get: freeze(() => {
        return value;
      }),
      set: freeze((newValue) => {
        value = newValue;
        for (const observe of observers) {
          observe(value);
        }
      }),
      observe: freeze((observe) => {
        observers.push(observe);
        observe(value);
      }),
      enumerable: true,
    });
  };

  const cells = [
    {
      globalThis: cell("globalThis"),
      Array: cell("Array"),
      ArrayBuffer: cell("ArrayBuffer"),
      Date: cell("Date"),
      FinalizationRegistry: cell("FinalizationRegistry"),
      Float32Array: cell("Float32Array"),
      JSON: cell("JSON"),
      Map: cell("Map"),
      Math: cell("Math"),
      Number: cell("Number"),
      Object: cell("Object"),
      Promise: cell("Promise"),
      Proxy: cell("Proxy"),
      Reflect: cell("Reflect"),
      FERAL_REG_EXP: cell("FERAL_REG_EXP"),
      Set: cell("Set"),
      String: cell("String"),
      Symbol: cell("Symbol"),
      Uint8Array: cell("Uint8Array"),
      WeakMap: cell("WeakMap"),
      WeakSet: cell("WeakSet"),
      FERAL_ERROR: cell("FERAL_ERROR"),
      RangeError: cell("RangeError"),
      ReferenceError: cell("ReferenceError"),
      SyntaxError: cell("SyntaxError"),
      TypeError: cell("TypeError"),
      AggregateError: cell("AggregateError"),
      assign: cell("assign"),
      create: cell("create"),
      defineProperties: cell("defineProperties"),
      entries: cell("entries"),
      freeze: cell("freeze"),
      getOwnPropertyDescriptor: cell("getOwnPropertyDescriptor"),
      getOwnPropertyDescriptors: cell("getOwnPropertyDescriptors"),
      getOwnPropertyNames: cell("getOwnPropertyNames"),
      getPrototypeOf: cell("getPrototypeOf"),
      is: cell("is"),
      isFrozen: cell("isFrozen"),
      isSealed: cell("isSealed"),
      isExtensible: cell("isExtensible"),
      keys: cell("keys"),
      objectPrototype: cell("objectPrototype"),
      seal: cell("seal"),
      preventExtensions: cell("preventExtensions"),
      setPrototypeOf: cell("setPrototypeOf"),
      values: cell("values"),
      fromEntries: cell("fromEntries"),
      speciesSymbol: cell("speciesSymbol"),
      toStringTagSymbol: cell("toStringTagSymbol"),
      iteratorSymbol: cell("iteratorSymbol"),
      matchAllSymbol: cell("matchAllSymbol"),
      replaceSymbol: cell("replaceSymbol"),
      unscopablesSymbol: cell("unscopablesSymbol"),
      symbolKeyFor: cell("symbolKeyFor"),
      symbolFor: cell("symbolFor"),
      isInteger: cell("isInteger"),
      stringifyJson: cell("stringifyJson"),
      defineProperty: cell("defineProperty"),
      apply: cell("apply"),
      construct: cell("construct"),
      reflectGet: cell("reflectGet"),
      reflectGetOwnPropertyDescriptor: cell("reflectGetOwnPropertyDescriptor"),
      reflectHas: cell("reflectHas"),
      reflectIsExtensible: cell("reflectIsExtensible"),
      ownKeys: cell("ownKeys"),
      reflectPreventExtensions: cell("reflectPreventExtensions"),
      reflectSet: cell("reflectSet"),
      isArray: cell("isArray"),
      arrayPrototype: cell("arrayPrototype"),
      arrayBufferPrototype: cell("arrayBufferPrototype"),
      mapPrototype: cell("mapPrototype"),
      proxyRevocable: cell("proxyRevocable"),
      regexpPrototype: cell("regexpPrototype"),
      setPrototype: cell("setPrototype"),
      stringPrototype: cell("stringPrototype"),
      weakmapPrototype: cell("weakmapPrototype"),
      weaksetPrototype: cell("weaksetPrototype"),
      functionPrototype: cell("functionPrototype"),
      promisePrototype: cell("promisePrototype"),
      generatorPrototype: cell("generatorPrototype"),
      iteratorPrototype: cell("iteratorPrototype"),
      typedArrayPrototype: cell("typedArrayPrototype"),
      uncurryThis: cell("uncurryThis"),
      hasOwn: cell("hasOwn"),
      arrayFilter: cell("arrayFilter"),
      arrayForEach: cell("arrayForEach"),
      arrayIncludes: cell("arrayIncludes"),
      arrayJoin: cell("arrayJoin"),
      arrayMap: cell("arrayMap"),
      arrayFlatMap: cell("arrayFlatMap"),
      arrayPop: cell("arrayPop"),
      arrayPush: cell("arrayPush"),
      arraySlice: cell("arraySlice"),
      arraySome: cell("arraySome"),
      arraySort: cell("arraySort"),
      iterateArray: cell("iterateArray"),
      arrayBufferSlice: cell("arrayBufferSlice"),
      arrayBufferGetByteLength: cell("arrayBufferGetByteLength"),
      typedArraySet: cell("typedArraySet"),
      mapSet: cell("mapSet"),
      mapGet: cell("mapGet"),
      mapHas: cell("mapHas"),
      mapDelete: cell("mapDelete"),
      mapEntries: cell("mapEntries"),
      iterateMap: cell("iterateMap"),
      setAdd: cell("setAdd"),
      setDelete: cell("setDelete"),
      setForEach: cell("setForEach"),
      setHas: cell("setHas"),
      iterateSet: cell("iterateSet"),
      regexpExec: cell("regexpExec"),
      regexpReplace: cell("regexpReplace"),
      matchAllRegExp: cell("matchAllRegExp"),
      sealRegexp: cell("sealRegexp"),
      stringEndsWith: cell("stringEndsWith"),
      stringIncludes: cell("stringIncludes"),
      stringIndexOf: cell("stringIndexOf"),
      stringMatch: cell("stringMatch"),
      stringSearch: cell("stringSearch"),
      stringSlice: cell("stringSlice"),
      stringSplit: cell("stringSplit"),
      stringStartsWith: cell("stringStartsWith"),
      iterateString: cell("iterateString"),
      weakmapDelete: cell("weakmapDelete"),
      weakmapGet: cell("weakmapGet"),
      weakmapHas: cell("weakmapHas"),
      weakmapSet: cell("weakmapSet"),
      weaksetAdd: cell("weaksetAdd"),
      weaksetHas: cell("weaksetHas"),
      functionToString: cell("functionToString"),
      functionBind: cell("functionBind"),
      generatorNext: cell("generatorNext"),
      generatorThrow: cell("generatorThrow"),
      promiseAll: cell("promiseAll"),
      promiseCatch: cell("promiseCatch"),
      promiseThen: cell("promiseThen"),
      finalizationRegistryRegister: cell("finalizationRegistryRegister"),
      finalizationRegistryUnregister: cell("finalizationRegistryUnregister"),
      isPrimitive: cell("isPrimitive"),
      isError: cell("isError"),
      identity: cell("identity"),
      FERAL_EVAL: cell("FERAL_EVAL"),
      FERAL_FUNCTION: cell("FERAL_FUNCTION"),
      noEvalEvaluate: cell("noEvalEvaluate"),
      FERAL_STACK_GETTER: cell("FERAL_STACK_GETTER"),
      FERAL_STACK_SETTER: cell("FERAL_STACK_SETTER"),
      AsyncGeneratorFunctionInstance: cell("AsyncGeneratorFunctionInstance"),
    },
    {
    },
    {
      makeEnvironmentCaptor: cell("makeEnvironmentCaptor"),
      getEnvironmentOption: cell("getEnvironmentOption"),
      getEnvironmentOptionsList: cell("getEnvironmentOptionsList"),
      environmentOptionsListHas: cell("environmentOptionsListHas"),
    },
    {
    },
    {
      isBufferImmutable: cell("isBufferImmutable"),
      sliceBufferToImmutable: cell("sliceBufferToImmutable"),
      optTransferBufferToImmutable: cell("optTransferBufferToImmutable"),
    },
    {
    },
    {
    },
    {
      an: cell("an"),
      bestEffortStringify: cell("bestEffortStringify"),
      enJoin: cell("enJoin"),
    },
    {
    },
    {
    },
    {
      makeCacheMapKit: cell("makeCacheMapKit"),
    },
    {
      makeCacheMapKit: cell("makeCacheMapKit"),
    },
    {
      makeNoteLogArgsArrayKit: cell("makeNoteLogArgsArrayKit"),
    },
    {
      q: cell("q"),
      b: cell("b"),
      X: cell("X"),
      unredactedDetails: cell("unredactedDetails"),
      makeError: cell("makeError"),
      annotateError: cell("annotateError"),
      loggedErrorHandler: cell("loggedErrorHandler"),
      assert: cell("assert"),
      assertEqual: cell("assertEqual"),
      sanitizeError: cell("sanitizeError"),
      makeAssert: cell("makeAssert"),
    },
    {
      isTypedArray: cell("isTypedArray"),
      makeHardener: cell("makeHardener"),
    },
    {
      cauterizeProperty: cell("cauterizeProperty"),
    },
    {
      NativeErrors: cell("NativeErrors"),
      constantProperties: cell("constantProperties"),
      universalPropertyNames: cell("universalPropertyNames"),
      initialGlobalPropertyNames: cell("initialGlobalPropertyNames"),
      sharedGlobalPropertyNames: cell("sharedGlobalPropertyNames"),
      uniqueGlobalPropertyNames: cell("uniqueGlobalPropertyNames"),
      FunctionInstance: cell("FunctionInstance"),
      AsyncFunctionInstance: cell("AsyncFunctionInstance"),
      isAccessorPermit: cell("isAccessorPermit"),
      permitted: cell("permitted"),
    },
    {
      makeIntrinsicsCollector: cell("makeIntrinsicsCollector"),
      getGlobalIntrinsics: cell("getGlobalIntrinsics"),
    },
    {
      default: cell("default"),
    },
    {
      default: cell("default"),
    },
    {
      default: cell("default"),
    },
    {
      default: cell("default"),
    },
    {
      default: cell("default"),
    },
    {
      minEnablements: cell("minEnablements"),
      moderateEnablements: cell("moderateEnablements"),
      severeEnablements: cell("severeEnablements"),
    },
    {
      default: cell("default"),
    },
    {
      default: cell("default"),
    },
    {
      makeEvalFunction: cell("makeEvalFunction"),
    },
    {
      makeFunctionConstructor: cell("makeFunctionConstructor"),
    },
    {
      setGlobalObjectSymbolUnscopables: cell("setGlobalObjectSymbolUnscopables"),
      setGlobalObjectConstantProperties: cell("setGlobalObjectConstantProperties"),
      setGlobalObjectMutableProperties: cell("setGlobalObjectMutableProperties"),
      setGlobalObjectEvaluators: cell("setGlobalObjectEvaluators"),
    },
    {
      alwaysThrowHandler: cell("alwaysThrowHandler"),
      strictScopeTerminatorHandler: cell("strictScopeTerminatorHandler"),
      strictScopeTerminator: cell("strictScopeTerminator"),
    },
    {
      createSloppyGlobalsScopeTerminator: cell("createSloppyGlobalsScopeTerminator"),
    },
    {
      makeEvalScopeKit: cell("makeEvalScopeKit"),
    },
    {
      getSourceURL: cell("getSourceURL"),
    },
    {
      rejectHtmlComments: cell("rejectHtmlComments"),
      evadeHtmlCommentTest: cell("evadeHtmlCommentTest"),
      rejectImportExpressions: cell("rejectImportExpressions"),
      evadeImportExpressionTest: cell("evadeImportExpressionTest"),
      rejectSomeDirectEvalExpressions: cell("rejectSomeDirectEvalExpressions"),
      mandatoryTransforms: cell("mandatoryTransforms"),
      applyTransforms: cell("applyTransforms"),
      transforms: cell("transforms"),
    },
    {
      isValidIdentifierName: cell("isValidIdentifierName"),
      getScopeConstants: cell("getScopeConstants"),
    },
    {
      makeEvaluate: cell("makeEvaluate"),
    },
    {
      makeSafeEvaluator: cell("makeSafeEvaluator"),
    },
    {
      tameFunctionToString: cell("tameFunctionToString"),
    },
    {
      tameDomains: cell("tameDomains"),
    },
    {
      tameModuleSource: cell("tameModuleSource"),
    },
    {
      consoleLevelMethods: cell("consoleLevelMethods"),
      consoleOtherMethods: cell("consoleOtherMethods"),
      makeLoggingConsoleKit: cell("makeLoggingConsoleKit"),
      pumpLogToConsole: cell("pumpLogToConsole"),
      makeCausalConsole: cell("makeCausalConsole"),
      defineCausalConsoleFromLogger: cell("defineCausalConsoleFromLogger"),
      filterConsole: cell("filterConsole"),
    },
    {
      makeRejectionHandlers: cell("makeRejectionHandlers"),
    },
    {
      tameConsole: cell("tameConsole"),
    },
    {
      filterFileName: cell("filterFileName"),
      shortenCallSiteString: cell("shortenCallSiteString"),
      tameV8ErrorConstructor: cell("tameV8ErrorConstructor"),
    },
    {
      default: cell("default"),
    },
    {
      makeAlias: cell("makeAlias"),
      load: cell("load"),
      loadNow: cell("loadNow"),
    },
    {
      deferExports: cell("deferExports"),
      getDeferredExports: cell("getDeferredExports"),
    },
    {
      provideCompartmentEvaluator: cell("provideCompartmentEvaluator"),
      compartmentEvaluate: cell("compartmentEvaluate"),
    },
    {
      makeVirtualModuleInstance: cell("makeVirtualModuleInstance"),
      makeModuleInstance: cell("makeModuleInstance"),
    },
    {
      link: cell("link"),
      instantiate: cell("instantiate"),
    },
    {
      InertCompartment: cell("InertCompartment"),
      CompartmentPrototype: cell("CompartmentPrototype"),
      compartmentOptions: cell("compartmentOptions"),
      makeCompartmentConstructor: cell("makeCompartmentConstructor"),
    },
    {
      getAnonymousIntrinsics: cell("getAnonymousIntrinsics"),
    },
    {
      tameHarden: cell("tameHarden"),
    },
    {
      tameSymbolConstructor: cell("tameSymbolConstructor"),
    },
    {
      tameFauxDataProperty: cell("tameFauxDataProperty"),
      tameFauxDataProperties: cell("tameFauxDataProperties"),
    },
    {
      tameRegeneratorRuntime: cell("tameRegeneratorRuntime"),
    },
    {
      shimArrayBufferTransfer: cell("shimArrayBufferTransfer"),
    },
    {
      chooseReporter: cell("chooseReporter"),
      reportInGroup: cell("reportInGroup"),
    },
    {
      repairIntrinsics: cell("repairIntrinsics"),
    },
    {
    },
    {
    },
    {
    },
    {
    },
    {
    },
  ];

  defineProperties(cells[3], getOwnPropertyDescriptors(cells[2]));

  defineProperties(cells[11], {"makeCacheMapKit": { value: cells[10]["makeCacheMapKit"] } });

  const namespaces = cells.map(cells => freeze(create(null, {
    ...cells,
    // Make this appear like an ESM module namespace object.
    [Symbol.toStringTag]: {
      value: 'Module',
      writable: false,
      enumerable: false,
      configurable: false,
    },
  })));

  for (let index = 0; index < namespaces.length; index += 1) {
    cells[index]['*'] = cell('*', namespaces[index]);
  }

function observeImports(map, importName, importIndex) {
  for (const [name, observers] of map.get(importName)) {
    const cell = cells[importIndex][name];
    if (cell === undefined) {
      throw new ReferenceError(`Cannot import name ${name} (has ${Object.getOwnPropertyNames(cells[importIndex]).join(', ')})`);
    }
    for (const observer of observers) {
      cell.observe(observer);
    }
  }
}

  functors[0]({
    imports(entries) {
      const map = new Map(entries);
    },
    liveVar: {
    },
    onceVar: {
      universalThis: cells[0].globalThis.set,
      Array: cells[0].Array.set,
      ArrayBuffer: cells[0].ArrayBuffer.set,
      Date: cells[0].Date.set,
      FinalizationRegistry: cells[0].FinalizationRegistry.set,
      Float32Array: cells[0].Float32Array.set,
      JSON: cells[0].JSON.set,
      Map: cells[0].Map.set,
      Math: cells[0].Math.set,
      Number: cells[0].Number.set,
      Object: cells[0].Object.set,
      Promise: cells[0].Promise.set,
      Proxy: cells[0].Proxy.set,
      Reflect: cells[0].Reflect.set,
      FERAL_REG_EXP: cells[0].FERAL_REG_EXP.set,
      Set: cells[0].Set.set,
      String: cells[0].String.set,
      Symbol: cells[0].Symbol.set,
      Uint8Array: cells[0].Uint8Array.set,
      WeakMap: cells[0].WeakMap.set,
      WeakSet: cells[0].WeakSet.set,
      FERAL_ERROR: cells[0].FERAL_ERROR.set,
      RangeError: cells[0].RangeError.set,
      ReferenceError: cells[0].ReferenceError.set,
      SyntaxError: cells[0].SyntaxError.set,
      TypeError: cells[0].TypeError.set,
      AggregateError: cells[0].AggregateError.set,
      assign: cells[0].assign.set,
      create: cells[0].create.set,
      defineProperties: cells[0].defineProperties.set,
      entries: cells[0].entries.set,
      freeze: cells[0].freeze.set,
      getOwnPropertyDescriptor: cells[0].getOwnPropertyDescriptor.set,
      getOwnPropertyDescriptors: cells[0].getOwnPropertyDescriptors.set,
      getOwnPropertyNames: cells[0].getOwnPropertyNames.set,
      getPrototypeOf: cells[0].getPrototypeOf.set,
      is: cells[0].is.set,
      isFrozen: cells[0].isFrozen.set,
      isSealed: cells[0].isSealed.set,
      isExtensible: cells[0].isExtensible.set,
      keys: cells[0].keys.set,
      objectPrototype: cells[0].objectPrototype.set,
      seal: cells[0].seal.set,
      preventExtensions: cells[0].preventExtensions.set,
      setPrototypeOf: cells[0].setPrototypeOf.set,
      values: cells[0].values.set,
      fromEntries: cells[0].fromEntries.set,
      speciesSymbol: cells[0].speciesSymbol.set,
      toStringTagSymbol: cells[0].toStringTagSymbol.set,
      iteratorSymbol: cells[0].iteratorSymbol.set,
      matchAllSymbol: cells[0].matchAllSymbol.set,
      replaceSymbol: cells[0].replaceSymbol.set,
      unscopablesSymbol: cells[0].unscopablesSymbol.set,
      symbolKeyFor: cells[0].symbolKeyFor.set,
      symbolFor: cells[0].symbolFor.set,
      isInteger: cells[0].isInteger.set,
      stringifyJson: cells[0].stringifyJson.set,
      defineProperty: cells[0].defineProperty.set,
      apply: cells[0].apply.set,
      construct: cells[0].construct.set,
      reflectGet: cells[0].reflectGet.set,
      reflectGetOwnPropertyDescriptor: cells[0].reflectGetOwnPropertyDescriptor.set,
      reflectHas: cells[0].reflectHas.set,
      reflectIsExtensible: cells[0].reflectIsExtensible.set,
      ownKeys: cells[0].ownKeys.set,
      reflectPreventExtensions: cells[0].reflectPreventExtensions.set,
      reflectSet: cells[0].reflectSet.set,
      isArray: cells[0].isArray.set,
      arrayPrototype: cells[0].arrayPrototype.set,
      arrayBufferPrototype: cells[0].arrayBufferPrototype.set,
      mapPrototype: cells[0].mapPrototype.set,
      proxyRevocable: cells[0].proxyRevocable.set,
      regexpPrototype: cells[0].regexpPrototype.set,
      setPrototype: cells[0].setPrototype.set,
      stringPrototype: cells[0].stringPrototype.set,
      weakmapPrototype: cells[0].weakmapPrototype.set,
      weaksetPrototype: cells[0].weaksetPrototype.set,
      functionPrototype: cells[0].functionPrototype.set,
      promisePrototype: cells[0].promisePrototype.set,
      generatorPrototype: cells[0].generatorPrototype.set,
      iteratorPrototype: cells[0].iteratorPrototype.set,
      typedArrayPrototype: cells[0].typedArrayPrototype.set,
      uncurryThis: cells[0].uncurryThis.set,
      hasOwn: cells[0].hasOwn.set,
      arrayFilter: cells[0].arrayFilter.set,
      arrayForEach: cells[0].arrayForEach.set,
      arrayIncludes: cells[0].arrayIncludes.set,
      arrayJoin: cells[0].arrayJoin.set,
      arrayMap: cells[0].arrayMap.set,
      arrayFlatMap: cells[0].arrayFlatMap.set,
      arrayPop: cells[0].arrayPop.set,
      arrayPush: cells[0].arrayPush.set,
      arraySlice: cells[0].arraySlice.set,
      arraySome: cells[0].arraySome.set,
      arraySort: cells[0].arraySort.set,
      iterateArray: cells[0].iterateArray.set,
      arrayBufferSlice: cells[0].arrayBufferSlice.set,
      arrayBufferGetByteLength: cells[0].arrayBufferGetByteLength.set,
      typedArraySet: cells[0].typedArraySet.set,
      mapSet: cells[0].mapSet.set,
      mapGet: cells[0].mapGet.set,
      mapHas: cells[0].mapHas.set,
      mapDelete: cells[0].mapDelete.set,
      mapEntries: cells[0].mapEntries.set,
      iterateMap: cells[0].iterateMap.set,
      setAdd: cells[0].setAdd.set,
      setDelete: cells[0].setDelete.set,
      setForEach: cells[0].setForEach.set,
      setHas: cells[0].setHas.set,
      iterateSet: cells[0].iterateSet.set,
      regexpExec: cells[0].regexpExec.set,
      regexpReplace: cells[0].regexpReplace.set,
      matchAllRegExp: cells[0].matchAllRegExp.set,
      sealRegexp: cells[0].sealRegexp.set,
      stringEndsWith: cells[0].stringEndsWith.set,
      stringIncludes: cells[0].stringIncludes.set,
      stringIndexOf: cells[0].stringIndexOf.set,
      stringMatch: cells[0].stringMatch.set,
      stringSearch: cells[0].stringSearch.set,
      stringSlice: cells[0].stringSlice.set,
      stringSplit: cells[0].stringSplit.set,
      stringStartsWith: cells[0].stringStartsWith.set,
      iterateString: cells[0].iterateString.set,
      weakmapDelete: cells[0].weakmapDelete.set,
      weakmapGet: cells[0].weakmapGet.set,
      weakmapHas: cells[0].weakmapHas.set,
      weakmapSet: cells[0].weakmapSet.set,
      weaksetAdd: cells[0].weaksetAdd.set,
      weaksetHas: cells[0].weaksetHas.set,
      functionToString: cells[0].functionToString.set,
      functionBind: cells[0].functionBind.set,
      generatorNext: cells[0].generatorNext.set,
      generatorThrow: cells[0].generatorThrow.set,
      promiseAll: cells[0].promiseAll.set,
      promiseCatch: cells[0].promiseCatch.set,
      promiseThen: cells[0].promiseThen.set,
      finalizationRegistryRegister: cells[0].finalizationRegistryRegister.set,
      finalizationRegistryUnregister: cells[0].finalizationRegistryUnregister.set,
      isPrimitive: cells[0].isPrimitive.set,
      isError: cells[0].isError.set,
      identity: cells[0].identity.set,
      FERAL_EVAL: cells[0].FERAL_EVAL.set,
      FERAL_FUNCTION: cells[0].FERAL_FUNCTION.set,
      noEvalEvaluate: cells[0].noEvalEvaluate.set,
      FERAL_STACK_GETTER: cells[0].FERAL_STACK_GETTER.set,
      FERAL_STACK_SETTER: cells[0].FERAL_STACK_SETTER.set,
      AsyncGeneratorFunctionInstance: cells[0].AsyncGeneratorFunctionInstance.set,
    },
    importMeta: {},
  });
  functors[1]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[2]({
    imports(entries) {
      const map = new Map(entries);
    },
    liveVar: {
    },
    onceVar: {
      makeEnvironmentCaptor: cells[2].makeEnvironmentCaptor.set,
      getEnvironmentOption: cells[2].getEnvironmentOption.set,
      getEnvironmentOptionsList: cells[2].getEnvironmentOptionsList.set,
      environmentOptionsListHas: cells[2].environmentOptionsListHas.set,
    },
    importMeta: {},
  });
  functors[3]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./src/env-options.js", 2);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[4]({
    imports(entries) {
      const map = new Map(entries);
    },
    liveVar: {
    },
    onceVar: {
      isBufferImmutable: cells[4].isBufferImmutable.set,
      sliceBufferToImmutable: cells[4].sliceBufferToImmutable.set,
      optTransferBufferToImmutable: cells[4].optTransferBufferToImmutable.set,
    },
    importMeta: {},
  });
  functors[5]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./immutable-arraybuffer-pony.js", 4);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[6]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./src/immutable-arraybuffer-shim.js", 5);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[7]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "../commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      an: cells[7].an.set,
      bestEffortStringify: cells[7].bestEffortStringify.set,
      enJoin: cells[7].enJoin.set,
    },
    importMeta: {},
  });
  functors[8]({
    imports(entries) {
      const map = new Map(entries);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[9]({
    imports(entries) {
      const map = new Map(entries);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[10]({
    imports(entries) {
      const map = new Map(entries);
    },
    liveVar: {
    },
    onceVar: {
      makeCacheMapKit: cells[10].makeCacheMapKit.set,
    },
    importMeta: {},
  });
  functors[11]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./src/cachemap.js", 10);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[12]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "@endo/cache-map", 11);
    },
    liveVar: {
    },
    onceVar: {
      makeNoteLogArgsArrayKit: cells[12].makeNoteLogArgsArrayKit.set,
    },
    importMeta: {},
  });
  functors[13]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "../commons.js", 0);
      observeImports(map, "./stringify-utils.js", 7);
      observeImports(map, "./types.js", 8);
      observeImports(map, "./internal-types.js", 9);
      observeImports(map, "./note-log-args.js", 12);
    },
    liveVar: {
    },
    onceVar: {
      quote: cells[13].q.set,
      bare: cells[13].b.set,
      redactedDetails: cells[13].X.set,
      unredactedDetails: cells[13].unredactedDetails.set,
      makeError: cells[13].makeError.set,
      note: cells[13].annotateError.set,
      loggedErrorHandler: cells[13].loggedErrorHandler.set,
      assert: cells[13].assert.set,
      assertEqual: cells[13].assertEqual.set,
      sanitizeError: cells[13].sanitizeError.set,
      makeAssert: cells[13].makeAssert.set,
    },
    importMeta: {},
  });
  functors[14]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      isTypedArray: cells[14].isTypedArray.set,
      makeHardener: cells[14].makeHardener.set,
    },
    importMeta: {},
  });
  functors[15]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      cauterizeProperty: cells[15].cauterizeProperty.set,
    },
    importMeta: {},
  });
  functors[16]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      NativeErrors: cells[16].NativeErrors.set,
      constantProperties: cells[16].constantProperties.set,
      universalPropertyNames: cells[16].universalPropertyNames.set,
      initialGlobalPropertyNames: cells[16].initialGlobalPropertyNames.set,
      sharedGlobalPropertyNames: cells[16].sharedGlobalPropertyNames.set,
      uniqueGlobalPropertyNames: cells[16].uniqueGlobalPropertyNames.set,
      FunctionInstance: cells[16].FunctionInstance.set,
      AsyncFunctionInstance: cells[16].AsyncFunctionInstance.set,
      isAccessorPermit: cells[16].isAccessorPermit.set,
      permitted: cells[16].permitted.set,
    },
    importMeta: {},
  });
  functors[17]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./cauterize-property.js", 15);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./permits.js", 16);
    },
    liveVar: {
    },
    onceVar: {
      makeIntrinsicsCollector: cells[17].makeIntrinsicsCollector.set,
      getGlobalIntrinsics: cells[17].getGlobalIntrinsics.set,
    },
    importMeta: {},
  });
  functors[18]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./permits.js", 16);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./cauterize-property.js", 15);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[18].default.set,
    },
    importMeta: {},
  });
  functors[19]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[19].default.set,
    },
    importMeta: {},
  });
  functors[20]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[20].default.set,
    },
    importMeta: {},
  });
  functors[21]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[21].default.set,
    },
    importMeta: {},
  });
  functors[22]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[22].default.set,
    },
    importMeta: {},
  });
  functors[23]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      minEnablements: cells[23].minEnablements.set,
      moderateEnablements: cells[23].moderateEnablements.set,
      severeEnablements: cells[23].severeEnablements.set,
    },
    importMeta: {},
  });
  functors[24]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./enablements.js", 23);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[24].default.set,
    },
    importMeta: {},
  });
  functors[25]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[25].default.set,
    },
    importMeta: {},
  });
  functors[26]({
    imports(entries) {
      const map = new Map(entries);
    },
    liveVar: {
    },
    onceVar: {
      makeEvalFunction: cells[26].makeEvalFunction.set,
    },
    importMeta: {},
  });
  functors[27]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      makeFunctionConstructor: cells[27].makeFunctionConstructor.set,
    },
    importMeta: {},
  });
  functors[28]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./make-eval-function.js", 26);
      observeImports(map, "./make-function-constructor.js", 27);
      observeImports(map, "./permits.js", 16);
    },
    liveVar: {
    },
    onceVar: {
      setGlobalObjectSymbolUnscopables: cells[28].setGlobalObjectSymbolUnscopables.set,
      setGlobalObjectConstantProperties: cells[28].setGlobalObjectConstantProperties.set,
      setGlobalObjectMutableProperties: cells[28].setGlobalObjectMutableProperties.set,
      setGlobalObjectEvaluators: cells[28].setGlobalObjectEvaluators.set,
    },
    importMeta: {},
  });
  functors[29]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      alwaysThrowHandler: cells[29].alwaysThrowHandler.set,
      strictScopeTerminatorHandler: cells[29].strictScopeTerminatorHandler.set,
      strictScopeTerminator: cells[29].strictScopeTerminator.set,
    },
    importMeta: {},
  });
  functors[30]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./strict-scope-terminator.js", 29);
    },
    liveVar: {
    },
    onceVar: {
      createSloppyGlobalsScopeTerminator: cells[30].createSloppyGlobalsScopeTerminator.set,
    },
    importMeta: {},
  });
  functors[31]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      makeEvalScopeKit: cells[31].makeEvalScopeKit.set,
    },
    importMeta: {},
  });
  functors[32]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      getSourceURL: cells[32].getSourceURL.set,
    },
    importMeta: {},
  });
  functors[33]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./get-source-url.js", 32);
    },
    liveVar: {
    },
    onceVar: {
      rejectHtmlComments: cells[33].rejectHtmlComments.set,
      evadeHtmlCommentTest: cells[33].evadeHtmlCommentTest.set,
      rejectImportExpressions: cells[33].rejectImportExpressions.set,
      evadeImportExpressionTest: cells[33].evadeImportExpressionTest.set,
      rejectSomeDirectEvalExpressions: cells[33].rejectSomeDirectEvalExpressions.set,
      mandatoryTransforms: cells[33].mandatoryTransforms.set,
      applyTransforms: cells[33].applyTransforms.set,
      transforms: cells[33].transforms.set,
    },
    importMeta: {},
  });
  functors[34]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      isValidIdentifierName: cells[34].isValidIdentifierName.set,
      getScopeConstants: cells[34].getScopeConstants.set,
    },
    importMeta: {},
  });
  functors[35]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./scope-constants.js", 34);
    },
    liveVar: {
    },
    onceVar: {
      makeEvaluate: cells[35].makeEvaluate.set,
    },
    importMeta: {},
  });
  functors[36]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./strict-scope-terminator.js", 29);
      observeImports(map, "./sloppy-globals-scope-terminator.js", 30);
      observeImports(map, "./eval-scope.js", 31);
      observeImports(map, "./transforms.js", 33);
      observeImports(map, "./make-evaluate.js", 35);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      makeSafeEvaluator: cells[36].makeSafeEvaluator.set,
    },
    importMeta: {},
  });
  functors[37]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      tameFunctionToString: cells[37].tameFunctionToString.set,
    },
    importMeta: {},
  });
  functors[38]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      tameDomains: cells[38].tameDomains.set,
    },
    importMeta: {},
  });
  functors[39]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      tameModuleSource: cells[39].tameModuleSource.set,
    },
    importMeta: {},
  });
  functors[40]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "../commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      consoleLevelMethods: cells[40].consoleLevelMethods.set,
      consoleOtherMethods: cells[40].consoleOtherMethods.set,
      makeLoggingConsoleKit: cells[40].makeLoggingConsoleKit.set,
      pumpLogToConsole: cells[40].pumpLogToConsole.set,
      makeCausalConsole: cells[40].makeCausalConsole.set,
      defineCausalConsoleFromLogger: cells[40].defineCausalConsoleFromLogger.set,
      filterConsole: cells[40].filterConsole.set,
    },
    importMeta: {},
  });
  functors[41]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "../commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      makeRejectionHandlers: cells[41].makeRejectionHandlers.set,
    },
    importMeta: {},
  });
  functors[42]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "../commons.js", 0);
      observeImports(map, "./assert.js", 13);
      observeImports(map, "./console.js", 40);
      observeImports(map, "./unhandled-rejection.js", 41);
    },
    liveVar: {
    },
    onceVar: {
      tameConsole: cells[42].tameConsole.set,
    },
    importMeta: {},
  });
  functors[43]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "../commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      filterFileName: cells[43].filterFileName.set,
      shortenCallSiteString: cells[43].shortenCallSiteString.set,
      tameV8ErrorConstructor: cells[43].tameV8ErrorConstructor.set,
    },
    importMeta: {},
  });
  functors[44]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "../commons.js", 0);
      observeImports(map, "../permits.js", 16);
      observeImports(map, "./tame-v8-error-constructor.js", 43);
    },
    liveVar: {
    },
    onceVar: {
      default: cells[44].default.set,
    },
    importMeta: {},
  });
  functors[45]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "@endo/env-options", 3);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      makeAlias: cells[45].makeAlias.set,
      load: cells[45].load.set,
      loadNow: cells[45].loadNow.set,
    },
    importMeta: {},
  });
  functors[46]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./module-load.js", 45);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      deferExports: cells[46].deferExports.set,
      getDeferredExports: cells[46].getDeferredExports.set,
    },
    importMeta: {},
  });
  functors[47]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./transforms.js", 33);
      observeImports(map, "./make-safe-evaluator.js", 36);
    },
    liveVar: {
    },
    onceVar: {
      provideCompartmentEvaluator: cells[47].provideCompartmentEvaluator.set,
      compartmentEvaluate: cells[47].compartmentEvaluate.set,
    },
    importMeta: {},
  });
  functors[48]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./error/assert.js", 13);
      observeImports(map, "./module-proxy.js", 46);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./compartment-evaluate.js", 47);
    },
    liveVar: {
    },
    onceVar: {
      makeVirtualModuleInstance: cells[48].makeVirtualModuleInstance.set,
      makeModuleInstance: cells[48].makeModuleInstance.set,
    },
    importMeta: {},
  });
  functors[49]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./error/assert.js", 13);
      observeImports(map, "./module-instance.js", 48);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      link: cells[49].link.set,
      instantiate: cells[49].instantiate.set,
    },
    importMeta: {},
  });
  functors[50]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./global-object.js", 28);
      observeImports(map, "./error/assert.js", 13);
      observeImports(map, "./permits.js", 16);
      observeImports(map, "./module-load.js", 45);
      observeImports(map, "./module-link.js", 49);
      observeImports(map, "./module-proxy.js", 46);
      observeImports(map, "./compartment-evaluate.js", 47);
      observeImports(map, "./make-safe-evaluator.js", 36);
    },
    liveVar: {
    },
    onceVar: {
      InertCompartment: cells[50].InertCompartment.set,
      CompartmentPrototype: cells[50].CompartmentPrototype.set,
      compartmentOptions: cells[50].compartmentOptions.set,
      makeCompartmentConstructor: cells[50].makeCompartmentConstructor.set,
    },
    importMeta: {},
  });
  functors[51]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./compartment.js", 50);
    },
    liveVar: {
    },
    onceVar: {
      getAnonymousIntrinsics: cells[51].getAnonymousIntrinsics.set,
    },
    importMeta: {},
  });
  functors[52]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      tameHarden: cells[52].tameHarden.set,
    },
    importMeta: {},
  });
  functors[53]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      tameSymbolConstructor: cells[53].tameSymbolConstructor.set,
    },
    importMeta: {},
  });
  functors[54]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      tameFauxDataProperty: cells[54].tameFauxDataProperty.set,
      tameFauxDataProperties: cells[54].tameFauxDataProperties.set,
    },
    importMeta: {},
  });
  functors[55]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      tameRegeneratorRuntime: cells[55].tameRegeneratorRuntime.set,
    },
    importMeta: {},
  });
  functors[56]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
    },
    liveVar: {
    },
    onceVar: {
      shimArrayBufferTransfer: cells[56].shimArrayBufferTransfer.set,
    },
    importMeta: {},
  });
  functors[57]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
      chooseReporter: cells[57].chooseReporter.set,
      reportInGroup: cells[57].reportInGroup.set,
    },
    importMeta: {},
  });
  functors[58]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "@endo/env-options", 3);
      observeImports(map, "@endo/immutable-arraybuffer/shim.js", 6);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./make-hardener.js", 14);
      observeImports(map, "./intrinsics.js", 17);
      observeImports(map, "./permits-intrinsics.js", 18);
      observeImports(map, "./tame-function-constructors.js", 19);
      observeImports(map, "./tame-date-constructor.js", 20);
      observeImports(map, "./tame-math-object.js", 21);
      observeImports(map, "./tame-regexp-constructor.js", 22);
      observeImports(map, "./enable-property-overrides.js", 24);
      observeImports(map, "./tame-locale-methods.js", 25);
      observeImports(map, "./global-object.js", 28);
      observeImports(map, "./make-safe-evaluator.js", 36);
      observeImports(map, "./permits.js", 16);
      observeImports(map, "./tame-function-tostring.js", 37);
      observeImports(map, "./tame-domains.js", 38);
      observeImports(map, "./tame-module-source.js", 39);
      observeImports(map, "./error/tame-console.js", 42);
      observeImports(map, "./error/tame-error-constructor.js", 44);
      observeImports(map, "./error/assert.js", 13);
      observeImports(map, "./get-anonymous-intrinsics.js", 51);
      observeImports(map, "./compartment.js", 50);
      observeImports(map, "./tame-harden.js", 52);
      observeImports(map, "./tame-symbol-constructor.js", 53);
      observeImports(map, "./tame-faux-data-properties.js", 54);
      observeImports(map, "./tame-regenerator-runtime.js", 55);
      observeImports(map, "./shim-arraybuffer-transfer.js", 56);
      observeImports(map, "./reporting.js", 57);
    },
    liveVar: {
    },
    onceVar: {
      repairIntrinsics: cells[58].repairIntrinsics.set,
    },
    importMeta: {},
  });
  functors[59]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./assert-sloppy-mode.js", 1);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./lockdown.js", 58);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[60]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./compartment.js", 50);
      observeImports(map, "./tame-function-tostring.js", 37);
      observeImports(map, "./intrinsics.js", 17);
      observeImports(map, "./reporting.js", 57);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[61]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[62]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./commons.js", 0);
      observeImports(map, "./error/console.js", 40);
      observeImports(map, "./error/assert.js", 13);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });
  functors[63]({
    imports(entries) {
      const map = new Map(entries);
      observeImports(map, "./src/lockdown-shim.js", 59);
      observeImports(map, "./src/compartment-shim.js", 60);
      observeImports(map, "./src/assert-shim.js", 61);
      observeImports(map, "./src/console-shim.js", 62);
    },
    liveVar: {
    },
    onceVar: {
    },
    importMeta: {},
  });

  return cells[cells.length - 1]['*'].get();
})([
// === 0. ses ./src/commons.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([]);/**
 * Captures native intrinsics during initialization, so vetted shims
 * (running between initialization of SES and calling lockdown) are free to
 * modify the environment without compromising the integrity of SES. For
 * example, a vetted shim can modify Object.assign because we capture and
 * export Object and assign here, then never again consult Object to get its
 * assign property.
 *
 * This pattern of use is enforced by eslint rules no-restricted-globals and
 * no-polymorphic-call.
 * We maintain the list of restricted globals in ../package.json.
 *
 * @module
 */

/* global globalThis */
/* eslint-disable no-restricted-globals */

// We cannot use globalThis as the local name since it would capture the
// lexical name.
const universalThis = globalThis;$h͏_once.universalThis(universalThis);


       const {
  Array,
  ArrayBuffer,
  Date,
  FinalizationRegistry,
  Float32Array,
  JSON,
  Map,
  Math,
  Number,
  Object,
  Promise,
  Proxy,
  Reflect,
  RegExp: FERAL_REG_EXP,
  Set,
  String,
  Symbol,
  Uint8Array,
  WeakMap,
  WeakSet,
} = globalThis;$h͏_once.Array(Array);$h͏_once.ArrayBuffer(ArrayBuffer);$h͏_once.Date(Date);$h͏_once.FinalizationRegistry(FinalizationRegistry);$h͏_once.Float32Array(Float32Array);$h͏_once.JSON(JSON);$h͏_once.Map(Map);$h͏_once.Math(Math);$h͏_once.Number(Number);$h͏_once.Object(Object);$h͏_once.Promise(Promise);$h͏_once.Proxy(Proxy);$h͏_once.Reflect(Reflect);$h͏_once.FERAL_REG_EXP(FERAL_REG_EXP);$h͏_once.Set(Set);$h͏_once.String(String);$h͏_once.Symbol(Symbol);$h͏_once.Uint8Array(Uint8Array);$h͏_once.WeakMap(WeakMap);$h͏_once.WeakSet(WeakSet);

       const {
  // The feral Error constructor is safe for internal use, but must not be
  // revealed to post-lockdown code in any compartment including the start
  // compartment since in V8 at least it bears stack inspection capabilities.
  Error: FERAL_ERROR,
  RangeError,
  ReferenceError,
  SyntaxError,
  TypeError,
  AggregateError,
} = globalThis;$h͏_once.FERAL_ERROR(FERAL_ERROR);$h͏_once.RangeError(RangeError);$h͏_once.ReferenceError(ReferenceError);$h͏_once.SyntaxError(SyntaxError);$h͏_once.TypeError(TypeError);$h͏_once.AggregateError(AggregateError);

       const {
  assign,
  create,
  defineProperties,
  entries,
  freeze,
  getOwnPropertyDescriptor,
  getOwnPropertyDescriptors,
  getOwnPropertyNames,
  getPrototypeOf,
  is,
  isFrozen,
  isSealed,
  isExtensible,
  keys,
  prototype: objectPrototype,
  seal,
  preventExtensions,
  setPrototypeOf,
  values,
  fromEntries,
} = Object;$h͏_once.assign(assign);$h͏_once.create(create);$h͏_once.defineProperties(defineProperties);$h͏_once.entries(entries);$h͏_once.freeze(freeze);$h͏_once.getOwnPropertyDescriptor(getOwnPropertyDescriptor);$h͏_once.getOwnPropertyDescriptors(getOwnPropertyDescriptors);$h͏_once.getOwnPropertyNames(getOwnPropertyNames);$h͏_once.getPrototypeOf(getPrototypeOf);$h͏_once.is(is);$h͏_once.isFrozen(isFrozen);$h͏_once.isSealed(isSealed);$h͏_once.isExtensible(isExtensible);$h͏_once.keys(keys);$h͏_once.objectPrototype(objectPrototype);$h͏_once.seal(seal);$h͏_once.preventExtensions(preventExtensions);$h͏_once.setPrototypeOf(setPrototypeOf);$h͏_once.values(values);$h͏_once.fromEntries(fromEntries);

       const {
  species: speciesSymbol,
  toStringTag: toStringTagSymbol,
  iterator: iteratorSymbol,
  matchAll: matchAllSymbol,
  replace: replaceSymbol,
  unscopables: unscopablesSymbol,
  keyFor: symbolKeyFor,
  for: symbolFor,
} = Symbol;$h͏_once.speciesSymbol(speciesSymbol);$h͏_once.toStringTagSymbol(toStringTagSymbol);$h͏_once.iteratorSymbol(iteratorSymbol);$h͏_once.matchAllSymbol(matchAllSymbol);$h͏_once.replaceSymbol(replaceSymbol);$h͏_once.unscopablesSymbol(unscopablesSymbol);$h͏_once.symbolKeyFor(symbolKeyFor);$h͏_once.symbolFor(symbolFor);

       const { isInteger } = Number;$h͏_once.isInteger(isInteger);

       const { stringify: stringifyJson } = JSON;

// Needed only for the Safari bug workaround below
$h͏_once.stringifyJson(stringifyJson);const{defineProperty:originalDefineProperty}=Object;

       const defineProperty = (object, prop, descriptor) => {
  // We used to do the following, until we had to reopen Safari bug
  // https://bugs.webkit.org/show_bug.cgi?id=222538#c17
  // Once this is fixed, we may restore it.
  // // Object.defineProperty is allowed to fail silently so we use
  // // Object.defineProperties instead.
  // return defineProperties(object, { [prop]: descriptor });

  // Instead, to workaround the Safari bug
  const result = originalDefineProperty(object, prop, descriptor);
  if (result !== object) {
    // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_DEFINE_PROPERTY_FAILED_SILENTLY.md
    throw TypeError(
      `Please report that the original defineProperty silently failed to set ${stringifyJson(
        String(prop),
      )}. (SES_DEFINE_PROPERTY_FAILED_SILENTLY)`,
    );
  }
  return result;
};$h͏_once.defineProperty(defineProperty);

       const {
  apply,
  construct,
  get: reflectGet,
  getOwnPropertyDescriptor: reflectGetOwnPropertyDescriptor,
  has: reflectHas,
  isExtensible: reflectIsExtensible,
  ownKeys,
  preventExtensions: reflectPreventExtensions,
  set: reflectSet,
} = Reflect;$h͏_once.apply(apply);$h͏_once.construct(construct);$h͏_once.reflectGet(reflectGet);$h͏_once.reflectGetOwnPropertyDescriptor(reflectGetOwnPropertyDescriptor);$h͏_once.reflectHas(reflectHas);$h͏_once.reflectIsExtensible(reflectIsExtensible);$h͏_once.ownKeys(ownKeys);$h͏_once.reflectPreventExtensions(reflectPreventExtensions);$h͏_once.reflectSet(reflectSet);

       const { isArray, prototype: arrayPrototype } = Array;$h͏_once.isArray(isArray);$h͏_once.arrayPrototype(arrayPrototype);
       const { prototype: arrayBufferPrototype } = ArrayBuffer;$h͏_once.arrayBufferPrototype(arrayBufferPrototype);
       const { prototype: mapPrototype } = Map;$h͏_once.mapPrototype(mapPrototype);
       const { revocable: proxyRevocable } = Proxy;$h͏_once.proxyRevocable(proxyRevocable);
       const { prototype: regexpPrototype } = RegExp;$h͏_once.regexpPrototype(regexpPrototype);
       const { prototype: setPrototype } = Set;$h͏_once.setPrototype(setPrototype);
       const { prototype: stringPrototype } = String;$h͏_once.stringPrototype(stringPrototype);
       const { prototype: weakmapPrototype } = WeakMap;$h͏_once.weakmapPrototype(weakmapPrototype);
       const { prototype: weaksetPrototype } = WeakSet;$h͏_once.weaksetPrototype(weaksetPrototype);
       const { prototype: functionPrototype } = Function;$h͏_once.functionPrototype(functionPrototype);
       const { prototype: promisePrototype } = Promise;$h͏_once.promisePrototype(promisePrototype);
       const { prototype: generatorPrototype } = getPrototypeOf(
  // eslint-disable-next-line no-empty-function, func-names
  function* () {},
);$h͏_once.generatorPrototype(generatorPrototype);
       const iteratorPrototype = getPrototypeOf(
  // eslint-disable-next-line @endo/no-polymorphic-call
  getPrototypeOf(arrayPrototype.values()),
);$h͏_once.iteratorPrototype(iteratorPrototype);

       const typedArrayPrototype = getPrototypeOf(Uint8Array.prototype);$h͏_once.typedArrayPrototype(typedArrayPrototype);

const { bind } = functionPrototype;

/**
 * uncurryThis()
 * Equivalent of: fn => (thisArg, ...args) => apply(fn, thisArg, args)
 *
 * See those reference for a complete explanation:
 * http://wiki.ecmascript.org/doku.php?id=conventions:safe_meta_programming
 * which only lives at
 * http://web.archive.org/web/20160805225710/http://wiki.ecmascript.org/doku.php?id=conventions:safe_meta_programming
 *
 * @type {<F extends (this: any, ...args: any[]) => any>(fn: F) => ((thisArg: ThisParameterType<F>, ...args: Parameters<F>) => ReturnType<F>)}
 */
       const uncurryThis = bind.bind(bind.call); // eslint-disable-line @endo/no-polymorphic-call

// See https://github.com/endojs/endo/issues/2930
$h͏_once.uncurryThis(uncurryThis);if(!('hasOwn'in Object)){
  const ObjectPrototypeHasOwnProperty = objectPrototype.hasOwnProperty;
  const hasOwnShim = (obj, key) => {
    if (obj === undefined || obj === null) {
      // We need to add this extra test because of differences in
      // the order in which `hasOwn` vs `hasOwnProperty` validates
      // arguments.
      throw TypeError('Cannot convert undefined or null to object');
    }
    return apply(ObjectPrototypeHasOwnProperty, obj, [key]);
  };
  defineProperty(Object, 'hasOwn', {
    value: hasOwnShim,
    writable: true,
    enumerable: false,
    configurable: true,
  });
}

       const { hasOwn } = Object;
//
$h͏_once.hasOwn(hasOwn);const arrayFilter=uncurryThis(arrayPrototype.filter);$h͏_once.arrayFilter(arrayFilter);
       const arrayForEach = uncurryThis(arrayPrototype.forEach);$h͏_once.arrayForEach(arrayForEach);
       const arrayIncludes = uncurryThis(arrayPrototype.includes);$h͏_once.arrayIncludes(arrayIncludes);
       const arrayJoin = uncurryThis(arrayPrototype.join);
/** @type {<T, U>(thisArg: readonly T[], callbackfn: (value: T, index: number, array: T[]) => U, cbThisArg?: any) => U[]} */$h͏_once.arrayJoin(arrayJoin);
       const arrayMap = /** @type {any} */ (uncurryThis(arrayPrototype.map));$h͏_once.arrayMap(arrayMap);
       const arrayFlatMap = /** @type {any} */ (
  uncurryThis(arrayPrototype.flatMap)
);$h͏_once.arrayFlatMap(arrayFlatMap);
       const arrayPop = uncurryThis(arrayPrototype.pop);
/** @type {<T>(thisArg: T[], ...items: T[]) => number} */$h͏_once.arrayPop(arrayPop);
       const arrayPush = uncurryThis(arrayPrototype.push);$h͏_once.arrayPush(arrayPush);
       const arraySlice = uncurryThis(arrayPrototype.slice);$h͏_once.arraySlice(arraySlice);
       const arraySome = uncurryThis(arrayPrototype.some);$h͏_once.arraySome(arraySome);
       const arraySort = uncurryThis(arrayPrototype.sort);$h͏_once.arraySort(arraySort);
       const iterateArray = uncurryThis(arrayPrototype[iteratorSymbol]);
//
$h͏_once.iterateArray(iterateArray);const arrayBufferSlice=uncurryThis(arrayBufferPrototype.slice);
/** @type {(b: ArrayBuffer) => number} */$h͏_once.arrayBufferSlice(arrayBufferSlice);
       const arrayBufferGetByteLength = uncurryThis(
  // @ts-expect-error we know it is there on all conforming platforms
  getOwnPropertyDescriptor(arrayBufferPrototype, 'byteLength').get,
);
//
$h͏_once.arrayBufferGetByteLength(arrayBufferGetByteLength);const typedArraySet=uncurryThis(typedArrayPrototype.set);
//
$h͏_once.typedArraySet(typedArraySet);const mapSet=uncurryThis(mapPrototype.set);$h͏_once.mapSet(mapSet);
       const mapGet = uncurryThis(mapPrototype.get);$h͏_once.mapGet(mapGet);
       const mapHas = uncurryThis(mapPrototype.has);$h͏_once.mapHas(mapHas);
       const mapDelete = uncurryThis(mapPrototype.delete);$h͏_once.mapDelete(mapDelete);
       const mapEntries = uncurryThis(mapPrototype.entries);$h͏_once.mapEntries(mapEntries);
       const iterateMap = uncurryThis(mapPrototype[iteratorSymbol]);
//
$h͏_once.iterateMap(iterateMap);const setAdd=uncurryThis(setPrototype.add);$h͏_once.setAdd(setAdd);
       const setDelete = uncurryThis(setPrototype.delete);$h͏_once.setDelete(setDelete);
       const setForEach = uncurryThis(setPrototype.forEach);$h͏_once.setForEach(setForEach);
       const setHas = uncurryThis(setPrototype.has);$h͏_once.setHas(setHas);
       const iterateSet = uncurryThis(setPrototype[iteratorSymbol]);
//
/**
 * `regexpExec` is provided in exclusion of `regexpTest`, which would be
 * vulnerable to RegExp.prototype poisoning.
 */$h͏_once.iterateSet(iterateSet);
       const regexpExec = uncurryThis(regexpPrototype.exec);
/**
 * @type { &
 *   ((thisArg: RegExp, string: string, replaceValue: string) => string) &
 *   ((thisArg: RegExp, string: string, replacer: (substring: string, ...args: any[]) => string) => string)
 * }
 */$h͏_once.regexpExec(regexpExec);
       const regexpReplace = /** @type {any} */ (
  uncurryThis(regexpPrototype[replaceSymbol])
);$h͏_once.regexpReplace(regexpReplace);
       const matchAllRegExp = uncurryThis(regexpPrototype[matchAllSymbol]);$h͏_once.matchAllRegExp(matchAllRegExp);
const { _regexpConstructor, ...regexpDescriptors } =
  getOwnPropertyDescriptors(regexpPrototype);
arrayForEach(ownKeys(regexpDescriptors), key => {
  const desc = regexpDescriptors[/** @type {any} */ (key)];
  desc.configurable = false;
  if (desc.writable) desc.writable = false;
});
/**
 * Protect a RegExp instance against RegExp.prototype poisoning ("exec",
 * "flags", Symbol.replace, etc.).
 * @type {<T extends RegExp>(regexp: T) => T}
 */
       const sealRegexp = regexp =>
  seal(defineProperties(regexp, regexpDescriptors));
//
$h͏_once.sealRegexp(sealRegexp);const stringEndsWith=uncurryThis(stringPrototype.endsWith);$h͏_once.stringEndsWith(stringEndsWith);
       const stringIncludes = uncurryThis(stringPrototype.includes);$h͏_once.stringIncludes(stringIncludes);
       const stringIndexOf = uncurryThis(stringPrototype.indexOf);$h͏_once.stringIndexOf(stringIndexOf);
       const stringMatch = uncurryThis(stringPrototype.match);
// `stringReplace` is intentionally omitted because it would be vulnerable to
// RegExp.prototype poisoning; use `regexpReplace(re, str, replacer)` instead
// (and `sealRegexp` on its regular expressions).
$h͏_once.stringMatch(stringMatch);const stringSearch=uncurryThis(stringPrototype.search);$h͏_once.stringSearch(stringSearch);
       const stringSlice = uncurryThis(stringPrototype.slice);
/**
 * `stringSplit` should only be used with a string separator; regular
 * expressions are vulnerable to RegExp.prototype poisoning.
 * @type {(thisArg: string, separator: string, limit?: number) => string[]}
 */$h͏_once.stringSlice(stringSlice);
       const stringSplit = /** @type {any} */ (
  uncurryThis(stringPrototype.split)
);$h͏_once.stringSplit(stringSplit);
       const stringStartsWith = uncurryThis(stringPrototype.startsWith);$h͏_once.stringStartsWith(stringStartsWith);
       const iterateString = uncurryThis(stringPrototype[iteratorSymbol]);
//
$h͏_once.iterateString(iterateString);const weakmapDelete=uncurryThis(weakmapPrototype.delete);
/** @type {<K extends {}, V>(thisArg: WeakMap<K, V>, ...args: Parameters<WeakMap<K,V>['get']>) => ReturnType<WeakMap<K,V>['get']>} */$h͏_once.weakmapDelete(weakmapDelete);
       const weakmapGet = uncurryThis(weakmapPrototype.get);$h͏_once.weakmapGet(weakmapGet);
       const weakmapHas = uncurryThis(weakmapPrototype.has);$h͏_once.weakmapHas(weakmapHas);
       const weakmapSet = uncurryThis(weakmapPrototype.set);
//
$h͏_once.weakmapSet(weakmapSet);const weaksetAdd=uncurryThis(weaksetPrototype.add);$h͏_once.weaksetAdd(weaksetAdd);
       const weaksetHas = uncurryThis(weaksetPrototype.has);
//
$h͏_once.weaksetHas(weaksetHas);const functionToString=uncurryThis(functionPrototype.toString);$h͏_once.functionToString(functionToString);
       const functionBind = uncurryThis(bind);
//
$h͏_once.functionBind(functionBind);const generatorNext=uncurryThis(generatorPrototype.next);$h͏_once.generatorNext(generatorNext);
       const generatorThrow = uncurryThis(generatorPrototype.throw);
//
$h͏_once.generatorThrow(generatorThrow);const{all}=Promise;
       const promiseAll = promises => apply(all, Promise, [promises]);$h͏_once.promiseAll(promiseAll);
       const promiseCatch = uncurryThis(promisePrototype.catch);
/** @type {<T, TResult1 = T, TResult2 = never>(thisArg: T, onfulfilled?: ((value: T) => TResult1 | PromiseLike<TResult1>) | undefined | null, onrejected?: ((reason: any) => TResult2 | PromiseLike<TResult2>) | undefined | null) => Promise<TResult1 | TResult2>} */$h͏_once.promiseCatch(promiseCatch);
       const promiseThen = /** @type {any} */ (
  uncurryThis(promisePrototype.then)
);
//
$h͏_once.promiseThen(promiseThen);const finalizationRegistryRegister=
  FinalizationRegistry && uncurryThis(FinalizationRegistry.prototype.register);$h͏_once.finalizationRegistryRegister(finalizationRegistryRegister);
       const finalizationRegistryUnregister =
  FinalizationRegistry &&
  uncurryThis(FinalizationRegistry.prototype.unregister);

/**
 * TODO Consolidate with `isPrimitive` that's currently in `@endo/pass-style`.
 * Layering constraints make this tricky, which is why we haven't yet figured
 * out how to do this.
 *
 * @type {(val: unknown) => val is (undefined
 * | null
 * | boolean
 * | number
 * | bigint
 * | string
 * | symbol)}
 */$h͏_once.finalizationRegistryUnregister(finalizationRegistryUnregister);
       const isPrimitive = val =>
  !val || (typeof val !== 'object' && typeof val !== 'function');

/**
 * isError tests whether an object inherits from the intrinsic
 * `Error.prototype`.
 * We capture the original error constructor as FERAL_ERROR to provide a clear
 * signal for reviewers that we are handling an object with excess authority,
 * like stack trace inspection, that we are carefully hiding from client code.
 * Checking instanceof happens to be safe, but to avoid uttering FERAL_ERROR
 * for such a trivial case outside commons.js, we provide a utility function.
 *
 * @param {any} value
 */$h͏_once.isPrimitive(isPrimitive);
       const isError = value => value instanceof FERAL_ERROR;

/**
 * @template T
 * @param {T} x
 */$h͏_once.isError(isError);
       const identity = x => x;

// The original unsafe untamed eval function, which must not escape.
// Sample at module initialization time, which is before lockdown can
// repair it.  Use it only to build powerless abstractions.
// eslint-disable-next-line no-eval
$h͏_once.identity(identity);const FERAL_EVAL=eval;

// The original unsafe untamed Function constructor, which must not escape.
// Sample at module initialization time, which is before lockdown can
// repair it.  Use it only to build powerless abstractions.
$h͏_once.FERAL_EVAL(FERAL_EVAL);const FERAL_FUNCTION=Function;$h͏_once.FERAL_FUNCTION(FERAL_FUNCTION);

       const noEvalEvaluate = () => {
  // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_NO_EVAL.md
  throw TypeError('Cannot eval with evalTaming set to "no-eval" (SES_NO_EVAL)');
};

// ////////////////// FERAL_STACK_GETTER FERAL_STACK_SETTER ////////////////////

// The error repair mechanism is very similar to code in
// pass-style/src/error.js and these implementations should be kept in sync.

/**
 * We gratuitiously construct a TypeError instance using syntax in order to
 * obviate the possibility that code that ran before SES (for which we are
 * irreducable vulnerable) may have replaced the global TypeError constructor.
 * We treat the nature of this error instance as the source of truth for the
 * nature of runtime constructed errors on the platform, particularly whether
 * such errors will have an own "stack" property with getters and setters.
 * At time of writing (2025) we know of no comparable mechanism for obtaining a
 * host-generated base Error instance, but we corroborate the nature of the
 * global Error constructor's instances and refuse to initialize SES in an
 * environment where the syntactic TypeError and global Error produce
 * inconsistent "stack" properties.
 * @returns {TypeError}
 */$h͏_once.noEvalEvaluate(noEvalEvaluate);
const makeTypeError = () => {
  try {
    // @ts-expect-error deliberate TypeError
    null.null;
    throw TypeError('obligatory'); // To convince the type flow inferrence.
  } catch (error) {
    return error;
  }
};

const errorStackDesc = getOwnPropertyDescriptor(Error('obligatory'), 'stack');
const typeErrorStackDesc = getOwnPropertyDescriptor(makeTypeError(), 'stack');

let feralStackGetter;
let feralStackSetter;
if (typeErrorStackDesc && typeErrorStackDesc.get) {
  // We should only encounter this case on v8 because of its problematic
  // error own stack accessor behavior.
  // Note that FF/SpiderMonkey, Moddable/XS, and the error stack proposal
  // all inherit a stack accessor property from Error.prototype, which is
  // great. That case needs no heroics to secure.
  if (
    // In the v8 case as we understand it, all errors have an own stack
    // accessor property, but within the same realm, all these accessor
    // properties have the same getter and have the same setter.
    // This is therefore the case that we repair.
    errorStackDesc &&
    typeof typeErrorStackDesc.get === 'function' &&
    typeErrorStackDesc.get === errorStackDesc.get &&
    typeof typeErrorStackDesc.set === 'function' &&
    typeErrorStackDesc.set === errorStackDesc.set
  ) {
    // Otherwise, we have own stack accessor properties that are outside
    // our expectations, that therefore need to be understood better
    // before we know how to repair them.
    feralStackGetter = freeze(typeErrorStackDesc.get);
    feralStackSetter = freeze(typeErrorStackDesc.set);
  } else {
    // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_UNEXPECTED_ERROR_OWN_STACK_ACCESSOR.md
    throw TypeError(
      'Unexpected Error own stack accessor functions (SES_UNEXPECTED_ERROR_OWN_STACK_ACCESSOR)',
    );
  }
}

/**
 * If on a v8 with the problematic error own stack accessor behavior,
 * `FERAL_STACK_GETTER` will be the shared getter of all those accessors
 * and `FERAL_STACK_SETTER` will be the shared setter. On any platform
 * without this problem, `FERAL_STACK_GETTER` and `FERAL_STACK_SETTER` are
 * both `undefined`.
 *
 * @type {(() => any) | undefined}
 */
       const FERAL_STACK_GETTER = feralStackGetter;

/**
 * If on a v8 with the problematic error own stack accessor behavior,
 * `FERAL_STACK_GETTER` will be the shared getter of all those accessors
 * and `FERAL_STACK_SETTER` will be the shared setter. On any platform
 * without this problem, `FERAL_STACK_GETTER` and `FERAL_STACK_SETTER` are
 * both `undefined`.
 *
 * @type {((newValue: any) => void) | undefined}
 */$h͏_once.FERAL_STACK_GETTER(FERAL_STACK_GETTER);
       const FERAL_STACK_SETTER = feralStackSetter;$h͏_once.FERAL_STACK_SETTER(FERAL_STACK_SETTER);

const getAsyncGeneratorFunctionInstance = () => {
  // Test for async generator function syntax support.
  try {
    // Wrapping one in an new Function lets the `hermesc` binary file
    // parse the Metro js bundle without SyntaxError, to generate the
    // optimised Hermes bytecode bundle, when `gradlew` is called to
    // assemble the release build APK for React Native prod Android apps.
    // Delaying the error until runtime lets us customise lockdown behaviour.
    return new FERAL_FUNCTION(
      'return (async function* AsyncGeneratorFunctionInstance() {})',
    )();
  } catch (error) {
    // Note: `Error.prototype.jsEngine` is only set by React Native runtime, not Hermes:
    // https://github.com/facebook/react-native/blob/main/packages/react-native/ReactCommon/hermes/executor/HermesExecutorFactory.cpp#L224-L230
    if (error.name === 'SyntaxError') {
      // Swallows Hermes error `async generators are unsupported` at runtime.
      // Note: `console` is not a JS built-in, so Hermes engine throws:
      // Uncaught ReferenceError: Property 'console' doesn't exist
      // See: https://github.com/facebook/hermes/issues/675
      // However React Native provides a `console` implementation when setting up error handling:
      // https://github.com/facebook/react-native/blob/main/packages/react-native/Libraries/Core/InitializeCore.js
      return undefined;
    } else if (error.name === 'EvalError') {
      // eslint-disable-next-line no-empty-function
      return async function* AsyncGeneratorFunctionInstance() {};
    } else {
      throw error;
    }
  }
};

/**
 * If the platform supports async generator functions, this will be an
 * async generator function instance. Otherwise, it will be `undefined`.
 *
 * @type {AsyncGeneratorFunction | undefined}
 */
       const AsyncGeneratorFunctionInstance =
  getAsyncGeneratorFunctionInstance();$h͏_once.AsyncGeneratorFunctionInstance(AsyncGeneratorFunctionInstance);
})()
,
// === 1. ses ./src/assert-sloppy-mode.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let TypeError;$h͏_imports([["./commons.js", [["TypeError",[$h͏_a => (TypeError = $h͏_a)]]]]]);

/** getThis returns globalThis in sloppy mode or undefined in strict mode. */
function getThis() {
  return this;
}

if (getThis()) {
  // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_NO_SLOPPY.md
  throw TypeError(`SES failed to initialize, sloppy mode (SES_NO_SLOPPY)`);
}
})()
,
// === 2. env-options ./src/env-options.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([]);/* global globalThis */
// @ts-check

// `@endo/env-options` needs to be imported quite early, and so should
// avoid importing from ses or anything that depends on ses.

// /////////////////////////////////////////////////////////////////////////////
// Prelude of cheap good - enough imitations of things we'd use or
// do differently if we could depend on ses

// eslint-disable-next-line no-restricted-globals
const localThis = globalThis;

const { Object, Reflect, Array, String, JSON, Error } = localThis;
const { freeze } = Object;
const { apply } = Reflect;

// Should be equivalent to the one in ses' commons.js even though it
// uses the other technique.
const uncurryThis =
  fn =>
  (receiver, ...args) =>
    apply(fn, receiver, args);
const arrayPush = uncurryThis(Array.prototype.push);
const arrayIncludes = uncurryThis(Array.prototype.includes);
const stringSplit = uncurryThis(String.prototype.split);

const q = JSON.stringify;

const Fail = (literals, ...args) => {
  let msg = literals[0];
  for (let i = 0; i < args.length; i += 1) {
    msg = `${msg}${args[i]}${literals[i + 1]}`;
  }
  throw Error(msg);
};

// end prelude
// /////////////////////////////////////////////////////////////////////////////

/**
 * `makeEnvironmentCaptor` provides a mechanism for getting environment
 * variables, if they are needed, and a way to catalog the names of all
 * the environment variables that were captured.
 *
 * @param {object} aGlobal
 * @param {boolean} [dropNames] Defaults to false. If true, don't track
 * names used.
 */
       const makeEnvironmentCaptor = (aGlobal, dropNames = false) => {
  /** @type {string[]} */
  const capturedEnvironmentOptionNames = [];

  /**
   * Gets an environment option by name and returns the option value or the
   * given default.
   *
   * @param {string} optionName
   * @param {string} defaultSetting
   * @param {string[]} [optOtherValues]
   * If provided, the option value must be included or match `defaultSetting`.
   * @returns {string}
   */
  const getEnvironmentOption = (
    optionName,
    defaultSetting,
    optOtherValues = undefined,
  ) => {
    typeof optionName === 'string' ||
      Fail`Environment option name ${q(optionName)} must be a string.`;
    typeof defaultSetting === 'string' ||
      Fail`Environment option default setting ${q(
        defaultSetting,
      )} must be a string.`;

    /** @type {string} */
    let setting = defaultSetting;
    const globalProcess = aGlobal.process || undefined;
    const globalEnv =
      (typeof globalProcess === 'object' && globalProcess.env) || undefined;
    if (typeof globalEnv === 'object') {
      if (optionName in globalEnv) {
        if (!dropNames) {
          arrayPush(capturedEnvironmentOptionNames, optionName);
        }
        const optionValue = globalEnv[optionName];
        // eslint-disable-next-line @endo/no-polymorphic-call
        typeof optionValue === 'string' ||
          Fail`Environment option named ${q(
            optionName,
          )}, if present, must have a corresponding string value, got ${q(
            optionValue,
          )}`;
        setting = optionValue;
      }
    }
    optOtherValues === undefined ||
      setting === defaultSetting ||
      arrayIncludes(optOtherValues, setting) ||
      Fail`Unrecognized ${q(optionName)} value ${q(
        setting,
      )}. Expected one of ${q([defaultSetting, ...optOtherValues])}`;
    return setting;
  };
  freeze(getEnvironmentOption);

  /**
   * @template {string} [T=string]
   * @param {string} optionName
   * @returns {T[]}
   */
  const getEnvironmentOptionsList = optionName => {
    const option = getEnvironmentOption(optionName, '');
    return freeze(option === '' ? [] : stringSplit(option, ','));
  };
  freeze(getEnvironmentOptionsList);

  /**
   * @template {string} [T=string]
   * @param {string} optionName
   * @param {T} element
   * @returns {boolean}
   */
  const environmentOptionsListHas = (optionName, element) =>
    arrayIncludes(getEnvironmentOptionsList(optionName), element);

  const getCapturedEnvironmentOptionNames = () => {
    return freeze([...capturedEnvironmentOptionNames]);
  };
  freeze(getCapturedEnvironmentOptionNames);

  return freeze({
    getEnvironmentOption,
    getEnvironmentOptionsList,
    environmentOptionsListHas,
    getCapturedEnvironmentOptionNames,
  });
};$h͏_once.makeEnvironmentCaptor(makeEnvironmentCaptor);
freeze(makeEnvironmentCaptor);

/**
 * For the simple case, where the global in question is `globalThis` and no
 * reporting of option names is desired.
 */
       const {
  getEnvironmentOption,
  getEnvironmentOptionsList,
  environmentOptionsListHas,
} = makeEnvironmentCaptor(localThis, true);$h͏_once.getEnvironmentOption(getEnvironmentOption);$h͏_once.getEnvironmentOptionsList(getEnvironmentOptionsList);$h͏_once.environmentOptionsListHas(environmentOptionsListHas);
})()
,
// === 3. env-options ./index.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([["./src/env-options.js", []]]);
})()
,
// === 4. immutable-arraybuffer ./src/immutable-arraybuffer-pony.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([]);/* global globalThis */

const {
  ArrayBuffer,
  Object,
  Reflect,
  Symbol,
  TypeError,
  Uint8Array,
  WeakMap,
  // Capture structuredClone before it can be scuttled.
  structuredClone: optStructuredClone
  // eslint-disable-next-line no-restricted-globals
} = globalThis;

const { freeze, defineProperty, getPrototypeOf, getOwnPropertyDescriptor } =
  Object;
const { apply, ownKeys } = Reflect;
const { toStringTag } = Symbol;

const { prototype: arrayBufferPrototype } = ArrayBuffer;
const { slice, transfer: optTransfer } = arrayBufferPrototype;
// @ts-expect-error TS doesn't know it'll be there
const { get: arrayBufferByteLength } = getOwnPropertyDescriptor(
  arrayBufferPrototype,
  'byteLength',
);

const typedArrayPrototype = getPrototypeOf(Uint8Array.prototype);
const { set: uint8ArraySet } = typedArrayPrototype;
// @ts-expect-error TS doesn't know it'll be there
const { get: uint8ArrayBuffer } = getOwnPropertyDescriptor(
  typedArrayPrototype,
  'buffer',
);

/**
 * Copy a range of values from a genuine ArrayBuffer exotic object into a new
 * ArrayBuffer.
 *
 * @param {ArrayBuffer} realBuffer
 * @param {number} [start]
 * @param {number} [end]
 * @returns {ArrayBuffer}
 */
const arrayBufferSlice = (realBuffer, start = undefined, end = undefined) =>
  apply(slice, realBuffer, [start, end]);

/**
 * Move the contents of a genuine ArrayBuffer exotic object into a new fresh
 * ArrayBuffer and detach the original source.
 * We can only do this on platforms that support `structuredClone` or
 * `ArrayBuffer.prototype.transfer`.
 * On other platforms, we can still emulate
 * `ArrayBuffer.prototoype.sliceToImmutable`, but not
 * `ArrayBuffer.prototype.transferToImmutable`.
 * Currently, these known-deficient platforms are
 * - Hermes
 * - Node.js <= 16
 * - Apparently some versions of JavaScriptCore that are still of concern.
 *
 * @param {ArrayBuffer} arrayBuffer
 * @returns {ArrayBuffer}
 */
let optArrayBufferTransfer;

if (optTransfer) {
  optArrayBufferTransfer = arrayBuffer => apply(optTransfer, arrayBuffer, []);
} else if (optStructuredClone) {
  optArrayBufferTransfer = arrayBuffer => {
    // Hopefully, a zero-length slice is cheap, but still enforces that
    // `arrayBuffer` is a genuine `ArrayBuffer` exotic object.
    arrayBufferSlice(arrayBuffer, 0, 0);
    return optStructuredClone(arrayBuffer, {
      transfer: [arrayBuffer],
    });
  };
} else {
  // Assignment is redundant, but remains for clarity.
  optArrayBufferTransfer = undefined;
}

/**
 * If we could use classes with private fields everywhere, this would have
 * been a `this.#buffer` private field on an `ImmutableArrayBufferInternal`
 * class. But we cannot do so on Hermes. So, instead, we
 * emulate the `this.#buffer` private field, including its use as a brand check.
 * Maps from all and only emulated Immutable ArrayBuffers to real ArrayBuffers.
 *
 * @type {Pick<WeakMap<ArrayBuffer, ArrayBuffer>, 'get' | 'has' | 'set'>}
 */
const buffers = new WeakMap();
// Avoid post-hoc prototype lookups.
for (const methodName of ['get', 'has', 'set']) {
  defineProperty(buffers, methodName, { value: buffers[methodName] });
}
const getBuffer = immuAB => {
  // Safe because this WeakMap owns its get method.
  // eslint-disable-next-line @endo/no-polymorphic-call
  const result = buffers.get(immuAB);
  if (result) {
    return result;
  }
  throw TypeError('Not an emulated Immutable ArrayBuffer');
};

// Omits `constructor` so `Array.prototype.constructor` is inherited.
const ImmutableArrayBufferInternalPrototype = {
  __proto__: arrayBufferPrototype,
  get byteLength() {
    return apply(arrayBufferByteLength, getBuffer(this), []);
  },
  get detached() {
    getBuffer(this); // shim brand check
    return false;
  },
  get maxByteLength() {
    // Not underlying maxByteLength, which is irrelevant
    return apply(arrayBufferByteLength, getBuffer(this), []);
  },
  get resizable() {
    getBuffer(this); // shim brand check
    return false;
  },
  get immutable() {
    getBuffer(this); // shim brand check
    return true;
  },
  slice(start = undefined, end = undefined) {
    return arrayBufferSlice(getBuffer(this), start, end);
  },
  sliceToImmutable(start = undefined, end = undefined) {
    // eslint-disable-next-line no-use-before-define
    return sliceBufferToImmutable(getBuffer(this), start, end);
  },
  resize(_newByteLength = undefined) {
    getBuffer(this); // shim brand check
    throw TypeError('Cannot resize an immutable ArrayBuffer');
  },
  transfer(_newLength = undefined) {
    getBuffer(this); // shim brand check
    throw TypeError('Cannot detach an immutable ArrayBuffer');
  },
  transferToFixedLength(_newLength = undefined) {
    getBuffer(this); // shim brand check
    throw TypeError('Cannot detach an immutable ArrayBuffer');
  },
  transferToImmutable(_newLength = undefined) {
    getBuffer(this); // shim brand check
    throw TypeError('Cannot detach an immutable ArrayBuffer');
  },
  /**
   * See https://github.com/endojs/endo/tree/master/packages/immutable-arraybuffer#purposeful-violation
   */
  [toStringTag]: 'ImmutableArrayBuffer',
};

// Better fidelity emulation of a class prototype
for (const key of ownKeys(ImmutableArrayBufferInternalPrototype)) {
  defineProperty(ImmutableArrayBufferInternalPrototype, key, {
    enumerable: false,
  });
}

/**
 * Emulates what would have been the encapsulated `ImmutableArrayBufferInternal`
 * class constructor. This function takes the `realBuffer` which its
 * result encapsulates. Security demands that this result has exclusive access
 * to the `realBuffer` it is given, which its callers must ensure.
 *
 * @param {ArrayBuffer} realBuffer
 * @returns {ArrayBuffer}
 */
const makeImmutableArrayBufferInternal = realBuffer => {
  const result = /** @type {ArrayBuffer} */ (
    /** @type {unknown} */ ({
      __proto__: ImmutableArrayBufferInternalPrototype,
    })
  );
  // Safe because this WeakMap owns its set method.
  // eslint-disable-next-line @endo/no-polymorphic-call
  buffers.set(result, realBuffer);
  return result;
};
// Since `makeImmutableArrayBufferInternal` MUST not escape,
// this `freeze` is just belt-and-suspenders.
freeze(makeImmutableArrayBufferInternal);

/**
 * @param {ArrayBuffer} buffer
 * @returns {boolean}
 */
// eslint-disable-next-line @endo/no-polymorphic-call
       const isBufferImmutable = buffer => buffers.has(buffer);

/**
 * Creates an immutable slice of the given buffer.
 * @param {ArrayBuffer} buffer The original buffer.
 * @param {number} [start] The start index.
 * @param {number} [end] The end index.
 * @returns {ArrayBuffer} The sliced immutable ArrayBuffer.
 */$h͏_once.isBufferImmutable(isBufferImmutable);
       const sliceBufferToImmutable = (
  buffer,
  start = undefined,
  end = undefined,
) => {
  // Safe because this WeakMap owns its get method.
  // eslint-disable-next-line @endo/no-polymorphic-call
  let realBuffer = buffers.get(buffer);
  if (realBuffer === undefined) {
    realBuffer = buffer;
  }
  return makeImmutableArrayBufferInternal(
    arrayBufferSlice(realBuffer, start, end),
  );
};$h͏_once.sliceBufferToImmutable(sliceBufferToImmutable);

let transferBufferToImmutable;
if (optArrayBufferTransfer) {
  /**
   * Transfer the contents to a new Immutable ArrayBuffer
   *
   * @param {ArrayBuffer} buffer The original buffer.
   * @param {number} [newLength] The start index.
   * @returns {ArrayBuffer}
   */
  transferBufferToImmutable = (buffer, newLength = undefined) => {
    if (newLength === undefined) {
      buffer = optArrayBufferTransfer(buffer);
    } else if (optTransfer) {
      buffer = apply(optTransfer, buffer, [newLength]);
    } else {
      buffer = optArrayBufferTransfer(buffer);
      const oldLength = buffer.byteLength;
      // eslint-disable-next-line @endo/restrict-comparison-operands
      if (newLength <= oldLength) {
        buffer = arrayBufferSlice(buffer, 0, newLength);
      } else {
        const oldTA = new Uint8Array(buffer);
        const newTA = new Uint8Array(newLength);
        apply(uint8ArraySet, newTA, [oldTA]);
        buffer = apply(uint8ArrayBuffer, newTA, []);
      }
    }
    const result = makeImmutableArrayBufferInternal(buffer);
    return /** @type {ArrayBuffer} */ (/** @type {unknown} */ (result));
  };
} else {
  transferBufferToImmutable = undefined;
}

       const optTransferBufferToImmutable = transferBufferToImmutable;$h͏_once.optTransferBufferToImmutable(optTransferBufferToImmutable);
})()
,
// === 5. immutable-arraybuffer ./src/immutable-arraybuffer-shim.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let isBufferImmutable,sliceBufferToImmutable,optXferBuf2Immu;$h͏_imports([["./immutable-arraybuffer-pony.js", [["isBufferImmutable",[$h͏_a => (isBufferImmutable = $h͏_a)]],["sliceBufferToImmutable",[$h͏_a => (sliceBufferToImmutable = $h͏_a)]],["optTransferBufferToImmutable",[$h͏_a => (optXferBuf2Immu = $h͏_a)]]]]]);







const {
  ArrayBuffer,
  JSON,
  Object,
  Reflect
  // eslint-disable-next-line no-restricted-globals
} = globalThis;

// Even though the imported one is not exported by the pony as a live binding,
// TS doesn't know that,
// so it cannot do its normal flow-based inference. By making and using a local
// copy, no problem.
const optTransferBufferToImmutable = optXferBuf2Immu;

const { getOwnPropertyDescriptors, defineProperties, defineProperty } = Object;
const { ownKeys } = Reflect;
const { prototype: arrayBufferPrototype } = ArrayBuffer;
const { stringify } = JSON;

const arrayBufferMethods = {
  /**
   * Creates an immutable slice of the given buffer.
   *
   * @this {ArrayBuffer} buffer The original buffer.
   * @param {number} [start] The start index.
   * @param {number} [end] The end index.
   * @returns {ArrayBuffer} The sliced immutable ArrayBuffer.
   */
  sliceToImmutable(start = undefined, end = undefined) {
    return sliceBufferToImmutable(this, start, end);
  },

  /**
   * @this {ArrayBuffer}
   */
  get immutable() {
    return isBufferImmutable(this);
  },

  ...(optTransferBufferToImmutable
    ? {
        /**
         * Transfer the contents to a new immutable ArrayBuffer
         *
         * @this {ArrayBuffer} buffer The original buffer.
         * @param {number} [newLength] The start index.
         * @returns {ArrayBuffer} The new immutable ArrayBuffer.
         */
        transferToImmutable(newLength = undefined) {
          return optTransferBufferToImmutable(this, newLength);
        },
      }
    : {}),
};

// Better fidelity emulation of a class prototype
for (const key of ownKeys(arrayBufferMethods)) {
  defineProperty(arrayBufferMethods, key, {
    enumerable: false,
  });
}

// Modern shim practice frowns on conditional installation, at least for
// proposals prior to stage 3. This is so changes to the proposal since
// an old shim was distributed don't need to worry about the proposal
// breaking old code depending on the old shim. Thus, if we detect that
// we're about to overwrite a prior installation, we simply issue this
// warning and continue.
//
// TODO, if the primordials are frozen after the prior implementation, such as
// by `lockdown`, then this precludes overwriting as expected. However, for
// this case, the following warning text will be confusing.
//
// Allowing polymorphic calls because these occur during initialization.
// eslint-disable-next-line @endo/no-polymorphic-call
const overwrites = ownKeys(arrayBufferMethods).filter(
  key => key in arrayBufferPrototype,
);
if (overwrites.length > 0) {
  // eslint-disable-next-line @endo/no-polymorphic-call
  console.warn(
    `About to overwrite ArrayBuffer.prototype properties ${stringify(overwrites)}`,
  );
}

defineProperties(
  arrayBufferPrototype,
  getOwnPropertyDescriptors(arrayBufferMethods),
);
})()
,
// === 6. immutable-arraybuffer ./shim.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([["./src/immutable-arraybuffer-shim.js", []]]);
})()
,
// === 7. ses ./src/error/stringify-utils.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Set,String,isArray,arrayJoin,arraySlice,arraySort,arrayMap,keys,fromEntries,freeze,is,isError,setAdd,setHas,stringIncludes,stringStartsWith,stringifyJson,toStringTagSymbol;$h͏_imports([["../commons.js", [["Set",[$h͏_a => (Set = $h͏_a)]],["String",[$h͏_a => (String = $h͏_a)]],["isArray",[$h͏_a => (isArray = $h͏_a)]],["arrayJoin",[$h͏_a => (arrayJoin = $h͏_a)]],["arraySlice",[$h͏_a => (arraySlice = $h͏_a)]],["arraySort",[$h͏_a => (arraySort = $h͏_a)]],["arrayMap",[$h͏_a => (arrayMap = $h͏_a)]],["keys",[$h͏_a => (keys = $h͏_a)]],["fromEntries",[$h͏_a => (fromEntries = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["is",[$h͏_a => (is = $h͏_a)]],["isError",[$h͏_a => (isError = $h͏_a)]],["setAdd",[$h͏_a => (setAdd = $h͏_a)]],["setHas",[$h͏_a => (setHas = $h͏_a)]],["stringIncludes",[$h͏_a => (stringIncludes = $h͏_a)]],["stringStartsWith",[$h͏_a => (stringStartsWith = $h͏_a)]],["stringifyJson",[$h͏_a => (stringifyJson = $h͏_a)]],["toStringTagSymbol",[$h͏_a => (toStringTagSymbol = $h͏_a)]]]]]);






















/** @import {Stringable} from '../../types.js' */

/**
 * Joins English terms with commas and an optional conjunction.
 *
 * @param {(string | Stringable)[]} terms
 * @param {"and" | "or"} conjunction
 */
       const enJoin = (terms, conjunction) => {
  if (terms.length === 0) {
    return '(none)';
  } else if (terms.length === 1) {
    return terms[0];
  } else if (terms.length === 2) {
    const [first, second] = terms;
    return `${first} ${conjunction} ${second}`;
  } else {
    return `${arrayJoin(arraySlice(terms, 0, -1), ', ')}, ${conjunction} ${
      terms[terms.length - 1]
    }`;
  }
};

/**
 * Prepend the correct indefinite article onto a noun, typically a typeof
 * result, e.g., "an object" vs. "a number"
 *
 * @param {string} str The noun to prepend
 * @returns {string} The noun prepended with a/an
 */$h͏_once.enJoin(enJoin);
const an = str => {
  str = `${str}`;
  if (str.length >= 1 && stringIncludes('aeiouAEIOU', str[0])) {
    return `an ${str}`;
  }
  return `a ${str}`;
};$h͏_once.an(an);
freeze(an);


/**
 * Like `JSON.stringify` but does not blow up if given a cycle or a bigint.
 * This is not
 * intended to be a serialization to support any useful unserialization,
 * or any programmatic use of the resulting string. The string is intended
 * *only* for showing a human under benign conditions, in order to be
 * informative enough for some
 * logging purposes. As such, this `bestEffortStringify` has an
 * imprecise specification and may change over time.
 *
 * The current `bestEffortStringify` possibly emits too many "seen"
 * markings: Not only for cycles, but also for repeated subtrees by
 * object identity.
 *
 * As a best effort only for diagnostic interpretation by humans,
 * `bestEffortStringify` also turns various cases that normal
 * `JSON.stringify` skips or errors on, like `undefined` or bigints,
 * into strings that convey their meaning. To distinguish this from
 * strings in the input, these synthesized strings always begin and
 * end with square brackets. To distinguish those strings from an
 * input string with square brackets, and input string that starts
 * with an open square bracket `[` is itself placed in square brackets.
 *
 * @param {any} payload
 * @param {(string|number)=} spaces
 * @returns {string}
 */
const bestEffortStringify = (payload, spaces = undefined) => {
  const seenSet = new Set();
  const replacer = (_, val) => {
    switch (typeof val) {
      case 'object': {
        if (val === null) {
          return null;
        }
        if (setHas(seenSet, val)) {
          return '[Seen]';
        }
        setAdd(seenSet, val);
        if (isError(val)) {
          return `[${val.name}: ${val.message}]`;
        }
        if (toStringTagSymbol in val) {
          // For the built-ins that have or inherit a `Symbol.toStringTag`-named
          // property, most of them inherit the default `toString` method,
          // which will print in a similar manner: `"[object Foo]"` vs
          // `"[Foo]"`. The exceptions are
          //    * `Symbol.prototype`, `BigInt.prototype`, `String.prototype`
          //      which don't matter to us since we handle primitives
          //      separately and we don't care about primitive wrapper objects.
          //    * TODO
          //      `Date.prototype`, `TypedArray.prototype`.
          //      Hmmm, we probably should make special cases for these. We're
          //      not using these yet, so it's not urgent. But others will run
          //      into these.
          //
          // Once #2018 is closed, the only objects in our code that have or
          // inherit a `Symbol.toStringTag`-named property are remotables
          // or their remote presences.
          // This printing will do a good job for these without
          // violating abstraction layering. This behavior makes sense
          // purely in terms of JavaScript concepts. That's some of the
          // motivation for choosing that representation of remotables
          // and their remote presences in the first place.
          return `[${val[toStringTagSymbol]}]`;
        }
        if (isArray(val)) {
          return val;
        }
        const names = keys(val);
        if (names.length < 2) {
          return val;
        }
        let sorted = true;
        for (let i = 1; i < names.length; i += 1) {
          if (names[i - 1] >= names[i]) {
            sorted = false;
            break;
          }
        }
        if (sorted) {
          return val;
        }
        arraySort(names);
        const entries = arrayMap(names, name => [name, val[name]]);
        return fromEntries(entries);
      }
      case 'function': {
        return `[Function ${val.name || '<anon>'}]`;
      }
      case 'string': {
        if (stringStartsWith(val, '[')) {
          return `[${val}]`;
        }
        return val;
      }
      case 'undefined':
      case 'symbol': {
        return `[${String(val)}]`;
      }
      case 'bigint': {
        return `[${val}n]`;
      }
      case 'number': {
        if (is(val, NaN)) {
          return '[NaN]';
        } else if (val === Infinity) {
          return '[Infinity]';
        } else if (val === -Infinity) {
          return '[-Infinity]';
        }
        return val;
      }
      default: {
        return val;
      }
    }
  };
  try {
    return stringifyJson(payload, replacer, spaces);
  } catch (_err) {
    // Don't do anything more fancy here if there is any
    // chance that might throw, unless you surround that
    // with another try-catch-recovery. For example,
    // the caught thing might be a proxy or other exotic
    // object rather than an error. The proxy might throw
    // whenever it is possible for it to.
    return '[Something that failed to stringify]';
  }
};$h͏_once.bestEffortStringify(bestEffortStringify);
freeze(bestEffortStringify);
})()
,
// === 8. ses ./src/error/types.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([]);// @ts-check

/** @import {GenericErrorConstructor, AssertMakeErrorOptions, DetailsToken, Stringable} from '../../types.js' */

/**
 * @typedef {object} VirtualConsole
 * @property {Console['debug']} debug
 * @property {Console['log']} log
 * @property {Console['info']} info
 * @property {Console['warn']} warn
 * @property {Console['error']} error
 *
 * @property {Console['trace']} trace
 * @property {Console['dirxml']} dirxml
 * @property {Console['group']} group
 * @property {Console['groupCollapsed']} groupCollapsed
 *
 * @property {Console['assert']} assert
 * @property {Console['timeLog']} timeLog
 *
 * @property {Console['clear']} clear
 * @property {Console['count']} count
 * @property {Console['countReset']} countReset
 * @property {Console['dir']} dir
 * @property {Console['groupEnd']} groupEnd
 *
 * @property {Console['table']} table
 * @property {Console['time']} time
 * @property {Console['timeEnd']} timeEnd
 * @property {Console['timeStamp']} timeStamp
 */

/* This is deliberately *not* JSDoc, it is a regular comment.
 *
 * TODO: We'd like to add the following properties to the above
 * VirtualConsole, but they currently cause conflicts where
 * some Typescript implementations don't have these properties
 * on the Console type.
 *
 * @property {Console['profile']} profile
 * @property {Console['profileEnd']} profileEnd
 */

/**
 * @typedef {'debug' | 'log' | 'info' | 'warn' | 'error'} LogSeverity
 */

/**
 * @typedef ConsoleFilter
 * @property {(severity: LogSeverity) => boolean} canLog
 */

/**
 * @callback FilterConsole
 * @param {VirtualConsole} baseConsole
 * @param {ConsoleFilter} filter
 * @param {string} [topic]
 * @returns {VirtualConsole}
 */
})()
,
// === 9. ses ./src/error/internal-types.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([]);// @ts-check

/**
 * @import {VirtualConsole} from './types.js'
 */

/**
 * @typedef {readonly any[]} LogArgs
 *
 * This is an array suitable to be used as arguments of a console
 * level message *after* the format string argument. It is the result of
 * a `details` template string and consists of alternating literal strings
 * and substitution values, starting with a literal string. At least that
 * first literal string is always present.
 */

/**
 * @callback NoteCallback
 *
 * @param {Error} error
 * @param {LogArgs} noteLogArgs
 * @returns {void}
 */

/**
 * @callback GetStackString
 * @param {Error} error
 * @returns {string=}
 */

/**
 * @typedef {object} LoggedErrorHandler
 *
 * Used to parameterize `makeCausalConsole` to give it access to potentially
 * hidden information to augment the logging of errors.
 *
 * @property {GetStackString} getStackString
 * @property {(error: Error) => string} tagError
 * @property {() => void} resetErrorTagNum for debugging purposes only
 * @property {(error: Error) => (LogArgs | undefined)} getMessageLogArgs
 * @property {(error: Error) => (LogArgs | undefined)} takeMessageLogArgs
 * @property {(error: Error, callback?: NoteCallback) => LogArgs[] } takeNoteLogArgsArray
 */

// /////////////////////////////////////////////////////////////////////////////

/**
 * @typedef {readonly [string, ...any[]]} LogRecord
 */

/**
 * @typedef {object} LoggingConsoleKit
 * @property {VirtualConsole} loggingConsole
 * @property {() => readonly LogRecord[]} takeLog
 */

/**
 * @typedef {object} MakeLoggingConsoleKitOptions
 * @property {boolean=} shouldResetForDebugging
 */

/**
 * @callback MakeLoggingConsoleKit
 *
 * A logging console just accumulates the contents of all permitted calls,
 * making them available to callers of `takeLog()`. Calling `takeLog()`
 * consumes these, so later calls to `takeLog()` will only provide a log of
 * calls that have happened since then.
 *
 * @param {LoggedErrorHandler} loggedErrorHandler
 * @param {MakeLoggingConsoleKitOptions=} options
 * @returns {LoggingConsoleKit}
 */

/**
 * @typedef {{
 *   NOTE: 'ERROR_NOTE:',
 *   MESSAGE: 'ERROR_MESSAGE:',
 *   CAUSE: 'cause:',
 *   ERRORS: 'errors:',
 * }} ErrorInfo
 */

/**
 * @typedef {ErrorInfo[keyof ErrorInfo]} ErrorInfoKind
 */

/**
 * @callback MakeCausalConsole
 *
 * Makes a causal console wrapper of a `baseConsole`, where the causal console
 * calls methods of the `loggedErrorHandler` to customize how it handles logged
 * errors.
 *
 * @param {VirtualConsole | undefined} baseConsole
 * @param {LoggedErrorHandler} loggedErrorHandler
 * @returns {VirtualConsole | undefined}
 */
})()
,
// === 10. cache-map ./src/cachemap.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([]);// @ts-check
/* global globalThis */
/* eslint-disable @endo/no-polymorphic-call */

// eslint-disable-next-line no-restricted-globals
const { Error, TypeError, WeakMap } = globalThis;
// eslint-disable-next-line no-restricted-globals
const { parse, stringify } = JSON;
// eslint-disable-next-line no-restricted-globals
const { isSafeInteger } = Number;
// eslint-disable-next-line no-restricted-globals
const { freeze } = Object;
// eslint-disable-next-line no-restricted-globals
const { toStringTag: toStringTagSymbol } = Symbol;

// eslint-disable-next-line no-restricted-globals
const UNKNOWN_KEY = Symbol('UNKNOWN_KEY');

/**
 * @template T
 * @typedef {T extends object ? { -readonly [K in keyof T]: T[K] } : never} WritableDeep
 *   Intentionally limited to local needs; refer to
 *   https://github.com/sindresorhus/type-fest if insufficient.
 */

/**
 * @template T
 * @param {T} value
 * @param {<U,>(name: string, value: U) => U} [reviver]
 * @returns {WritableDeep<T>}
 */
const deepCopyJsonable = (value, reviver) => {
  const encoded = stringify(value);
  const decoded = parse(encoded, reviver);
  return decoded;
};

const freezingReviver = (_name, value) => freeze(value);

/** @type {<T,>(value: T) => T} */
const deepCopyAndFreezeJsonable = value =>
  deepCopyJsonable(value, freezingReviver);

/**
 * A cache of bounded size, implementing the WeakMap interface but holding keys
 * strongly if created with a non-weak `makeMap` option of
 * {@link makeCacheMapKit}.
 *
 * @template K
 * @template V
 * @typedef {Pick<Map<K, V>, Exclude<keyof WeakMap<WeakKey, *>, 'set'>> & {set: (key: K, value: V) => WeakMapAPI<K, V>}} WeakMapAPI
 */

/**
 * @template K
 * @template V
 * @typedef {WeakMapAPI<K, V> & ({clear?: undefined} | Pick<Map<K, V>, 'clear'>)} SingleEntryMap
 */

/**
 * A cell of a doubly-linked ring (circular list) for a cache map.
 * Instances are not frozen, and so should be closely encapsulated.
 *
 * @template K
 * @template V
 * @typedef {object} CacheMapCell
 * @property {number} id for debugging
 * @property {CacheMapCell<K, V>} next
 * @property {CacheMapCell<K, V>} prev
 * @property {SingleEntryMap<K, V>} data
 */

/**
 * @template K
 * @template V
 * @param {CacheMapCell<K, V>} prev
 * @param {number} id
 * @param {SingleEntryMap<K, V>} data
 * @returns {CacheMapCell<K, V>}
 */
const appendNewCell = (prev, id, data) => {
  const next = prev?.next;
  const cell = { id, next, prev, data };
  prev.next = cell;
  next.prev = cell;
  return cell;
};

/**
 * @template K
 * @template V
 * @param {CacheMapCell<K, V>} cell
 * @param {CacheMapCell<K, V>} prev
 * @param {CacheMapCell<K, V>} [next]
 */
const moveCellAfter = (cell, prev, next = prev.next) => {
  if (cell === prev || cell === next) return; // already in position

  // Splice out cell.
  const { prev: oldPrev, next: oldNext } = cell;
  oldPrev.next = oldNext;
  oldNext.prev = oldPrev;

  // Splice in cell after prev.
  cell.prev = prev;
  cell.next = next;
  prev.next = cell;
  next.prev = cell;
};

/**
 * Clear out a cell to prepare it for future use. Its map is preserved when
 * possible, but must instead be replaced if the associated key is not known.
 *
 * @template K
 * @template V
 * @param {CacheMapCell<K, V>} cell
 * @param {K | UNKNOWN_KEY} oldKey
 * @param {() => SingleEntryMap<K, V>} [makeMap] required when the key is unknown
 */
const resetCell = (cell, oldKey, makeMap) => {
  if (oldKey !== UNKNOWN_KEY) {
    cell.data.delete(oldKey);
    return;
  }
  if (cell.data.clear) {
    cell.data.clear();
    return;
  }
  // WeakMap instances must be replaced when the key is unknown.
  if (!makeMap) {
    throw Error('internal: makeMap is required with UNKNOWN_KEY');
  }
  cell.data = makeMap();
};

const zeroMetrics = freeze({
  totalQueryCount: 0,
  totalHitCount: 0
  // TODO?
  // * method-specific counts
  // * liveTouchStats/evictedTouchStats { count, sum, mean, min, max }
  //   * p50/p90/p95/p99 via Ben-Haim/Tom-Tov streaming histograms
});
/** @typedef {typeof zeroMetrics} CacheMapMetrics */

/**
 * @template {MapConstructor | WeakMapConstructor} [C=WeakMapConstructor]
 * @template {Parameters<InstanceType<C>['set']>[0]} [K=Parameters<InstanceType<C>['set']>[0]]
 * @template {unknown} [V=unknown]
 * @typedef {object} CacheMapKit
 * @property {WeakMapAPI<K, V>} cache
 * @property {() => CacheMapMetrics} getMetrics
 */

/**
 * Create a bounded-size cache having WeakMap-compatible
 * `has`/`get`/`set`/`delete` methods, capable of supporting SES (specifically
 * `assert` error notes).
 * Key validity, comparison, and referential strength are controlled by the
 * `makeMap` option, which defaults to `WeakMap` but can be set to any producer
 * of objects with those methods (e.g., using `Map` allows for arbitrary keys
 * which will be strongly held).
 * Cache eviction policy is not currently configurable, but strives for a hit
 * ratio at least as good as
 * [LRU](https://en.wikipedia.org/wiki/Cache_replacement_policies#LRU) (e.g., it
 * might be
 * [CLOCK](https://en.wikipedia.org/wiki/Page_replacement_algorithm#Clock)
 * or [SIEVE](https://sievecache.com/)).
 *
 * @template {MapConstructor | WeakMapConstructor} [C=WeakMapConstructor]
 * @template {Parameters<InstanceType<C>['set']>[0]} [K=Parameters<InstanceType<C>['set']>[0]]
 * @template {unknown} [V=unknown]
 * @param {number} capacity
 * @param {object} [options]
 * @param {C | (() => SingleEntryMap<K, V>)} [options.makeMap]
 * @returns {CacheMapKit<C, K, V>}
 */
       const makeCacheMapKit = (capacity, options = {}) => {
  if (!isSafeInteger(capacity) || capacity < 0) {
    throw TypeError(
      'capacity must be a non-negative safe integer number <= 2**53 - 1',
    );
  }

  /**
   * @template V
   * @type {<V,>() => SingleEntryMap<K, V>}
   */
  const makeMap = (MaybeCtor => {
    try {
      // @ts-expect-error
      MaybeCtor();
      return /** @type {any} */ (MaybeCtor);
    } catch (err) {
      // @ts-expect-error
      const constructNewMap = () => new MaybeCtor();
      return constructNewMap;
    }
  })(options.makeMap ?? WeakMap);
  const tag =
    /** @type {any} */ (makeMap()).clear === undefined
      ? 'WeakCacheMap'
      : 'CacheMap';

  /** @type {WeakMapAPI<K, CacheMapCell<K, V>>} */
  const keyToCell = makeMap();
  // @ts-expect-error this sentinel head is special
  const head = /** @type {CacheMapCell<K, V>} */ ({
    id: 0,
    // next and prev are established below as self-referential.
    next: undefined,
    prev: undefined,
    data: {
      has: () => {
        throw Error('internal: sentinel head cell has no data');
      },
    },
  });
  head.next = head;
  head.prev = head;
  let cellCount = 0;

  const metrics = deepCopyJsonable(zeroMetrics);
  const getMetrics = () => deepCopyAndFreezeJsonable(metrics);

  /**
   * Touching moves a cell to first position so LRU eviction can target the last
   * cell (`head.prev`).
   *
   * @type {(key: K) => (CacheMapCell<K, V> | undefined)}
   */
  const touchKey = key => {
    metrics.totalQueryCount += 1;
    const cell = keyToCell.get(key);
    if (!cell?.data.has(key)) return undefined;

    metrics.totalHitCount += 1;
    moveCellAfter(cell, head);
    return cell;
  };

  /** @type {WeakMapAPI<K, V>['has']} */
  const has = key => {
    const cell = touchKey(key);
    return cell !== undefined;
  };
  freeze(has);

  /** @type {WeakMapAPI<K, V>['get']} */
  const get = key => {
    const cell = touchKey(key);
    return cell?.data.get(key);
  };
  freeze(get);

  /** @type {WeakMapAPI<K, V>['set']} */
  const set = (key, value) => {
    let cell = touchKey(key);
    if (cell) {
      cell.data.set(key, value);
      // eslint-disable-next-line no-use-before-define
      return implementation;
    }

    if (cellCount < capacity) {
      // Add and use a new cell at first position.
      cell = appendNewCell(head, cellCount + 1, makeMap());
      cellCount += 1; // intentionally follows cell creation
      cell.data.set(key, value);
    } else if (capacity > 0) {
      // Reuse the current tail, moving it to first position.
      cell = head.prev;
      resetCell(/** @type {any} */ (cell), UNKNOWN_KEY, makeMap);
      cell.data.set(key, value);
      moveCellAfter(cell, head);
    }

    // Don't establish this entry until prior steps succeed.
    if (cell) keyToCell.set(key, cell);

    // eslint-disable-next-line no-use-before-define
    return implementation;
  };
  freeze(set);

  // "delete" is a keyword.
  const { delete: deleteEntry } = {
    /** @type {WeakMapAPI<K, V>['delete']} */
    delete: key => {
      const cell = keyToCell.get(key);
      if (!cell?.data.has(key)) {
        keyToCell.delete(key);
        return false;
      }
      moveCellAfter(cell, head.prev);
      resetCell(cell, key);
      keyToCell.delete(key);
      return true;
    },
  };
  freeze(deleteEntry);

  const implementation = /** @type {WeakMapAPI<K, V>} */ ({
    has,
    get,
    set,
    delete: deleteEntry,
    // eslint-disable-next-line jsdoc/check-types
    [/** @type {typeof Symbol.toStringTag} */ (toStringTagSymbol)]: tag,
  });
  freeze(implementation);

  const kit = { cache: implementation, getMetrics };
  return freeze(kit);
};$h͏_once.makeCacheMapKit(makeCacheMapKit);
freeze(makeCacheMapKit);
})()
,
// === 11. cache-map ./index.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([["./src/cachemap.js", []]]);
})()
,
// === 12. ses ./src/error/note-log-args.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let makeCacheMapKit;$h͏_imports([["@endo/cache-map", [["makeCacheMapKit",[$h͏_a => (makeCacheMapKit = $h͏_a)]]]]]);





/**
 * @import {CacheMapKit} from '@endo/cache-map';
 * @import {LogArgs} from './internal-types.js';
 */

const { freeze } = Object;
const { isSafeInteger } = Number;

const defaultLoggedErrorsBudget = 1000;
const defaultArgsPerErrorBudget = 100;

/**
 * @param {number} [errorsBudget]
 * @param {number} [argsPerErrorBudget]
 */
       const makeNoteLogArgsArrayKit = (
  errorsBudget = defaultLoggedErrorsBudget,
  argsPerErrorBudget = defaultArgsPerErrorBudget,
) => {
  if (!isSafeInteger(argsPerErrorBudget) || argsPerErrorBudget < 1) {
    throw TypeError(
      'argsPerErrorBudget must be a safe positive integer number',
    );
  }

  /**
   * Maps from an error to an array of log args, where each log args is
   * remembered as an annotation on that error. This can be used, for example,
   * to keep track of additional causes of the error. The elements of any
   * log args may include errors which are associated with further annotations.
   * An augmented console, like the causal console of `console.js`, could
   * then retrieve the graph of such annotations.
   *
   * @type {CacheMapKit<WeakMapConstructor, Error, LogArgs[]>}
   */
  const { cache: noteLogArgsArrayMap } = makeCacheMapKit(errorsBudget);

  /**
   * @param {Error} error
   * @param {LogArgs} logArgs
   */
  const addLogArgs = (error, logArgs) => {
    const logArgsArray = noteLogArgsArrayMap.get(error);
    if (logArgsArray !== undefined) {
      if (logArgsArray.length >= argsPerErrorBudget) {
        logArgsArray.shift();
      }
      logArgsArray.push(logArgs);
    } else {
      noteLogArgsArrayMap.set(error, [logArgs]);
    }
  };
  freeze(addLogArgs);

  /**
   * @param {Error} error
   * @returns {LogArgs[] | undefined}
   */
  const takeLogArgsArray = error => {
    const result = noteLogArgsArrayMap.get(error);
    noteLogArgsArrayMap.delete(error);
    return result;
  };
  freeze(takeLogArgsArray);

  return freeze({
    addLogArgs,
    takeLogArgsArray,
  });
};$h͏_once.makeNoteLogArgsArrayKit(makeNoteLogArgsArrayKit);
freeze(makeNoteLogArgsArrayKit);
})()
,
// === 13. ses ./src/error/assert.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let RangeError,TypeError,WeakMap,arrayJoin,arrayMap,arrayPop,arrayPush,assign,freeze,defineProperty,globalThis,is,isError,regexpExec,regexpReplace,sealRegexp,stringIndexOf,stringSlice,stringStartsWith,weakmapDelete,weakmapGet,weakmapHas,weakmapSet,AggregateError,getOwnPropertyDescriptors,ownKeys,create,objectPrototype,hasOwn,an,bestEffortStringify,makeNoteLogArgsArrayKit;$h͏_imports([["../commons.js", [["RangeError",[$h͏_a => (RangeError = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["WeakMap",[$h͏_a => (WeakMap = $h͏_a)]],["arrayJoin",[$h͏_a => (arrayJoin = $h͏_a)]],["arrayMap",[$h͏_a => (arrayMap = $h͏_a)]],["arrayPop",[$h͏_a => (arrayPop = $h͏_a)]],["arrayPush",[$h͏_a => (arrayPush = $h͏_a)]],["assign",[$h͏_a => (assign = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["is",[$h͏_a => (is = $h͏_a)]],["isError",[$h͏_a => (isError = $h͏_a)]],["regexpExec",[$h͏_a => (regexpExec = $h͏_a)]],["regexpReplace",[$h͏_a => (regexpReplace = $h͏_a)]],["sealRegexp",[$h͏_a => (sealRegexp = $h͏_a)]],["stringIndexOf",[$h͏_a => (stringIndexOf = $h͏_a)]],["stringSlice",[$h͏_a => (stringSlice = $h͏_a)]],["stringStartsWith",[$h͏_a => (stringStartsWith = $h͏_a)]],["weakmapDelete",[$h͏_a => (weakmapDelete = $h͏_a)]],["weakmapGet",[$h͏_a => (weakmapGet = $h͏_a)]],["weakmapHas",[$h͏_a => (weakmapHas = $h͏_a)]],["weakmapSet",[$h͏_a => (weakmapSet = $h͏_a)]],["AggregateError",[$h͏_a => (AggregateError = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]],["ownKeys",[$h͏_a => (ownKeys = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["objectPrototype",[$h͏_a => (objectPrototype = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]]]],["./stringify-utils.js", [["an",[$h͏_a => (an = $h͏_a)]],["bestEffortStringify",[$h͏_a => (bestEffortStringify = $h͏_a)]]]],["./types.js", []],["./internal-types.js", []],["./note-log-args.js", [["makeNoteLogArgsArrayKit",[$h͏_a => (makeNoteLogArgsArrayKit = $h͏_a)]]]]]);
















































/**
 * @import {BaseAssert, Assert, AssertionFunctions, AssertionUtilities, DeprecatedAssertionUtilities, Stringable, DetailsToken, MakeAssert} from '../../types.js';
 * @import {LogArgs, NoteCallback, LoggedErrorHandler} from './internal-types.js';
 */

// For internal debugging purposes, uncomment
// const internalDebugConsole = console;

// /////////////////////////////////////////////////////////////////////////////

/**
 * Maps the result of a `quote` or `bare` call back to its input value.
 *
 * @type {WeakMap<Stringable, any>}
 */
const declassifiers = new WeakMap();

/** @type {AssertionUtilities['quote']} */
const quote = (value, spaces = undefined) => {
  const result = freeze({
    toString: freeze(() => bestEffortStringify(value, spaces)),
  });
  weakmapSet(declassifiers, result, value);
  return result;
};$h͏_once.quote(quote);
freeze(quote);

const canBeBare = freeze(/^[\w:-]( ?[\w:-])*$/);

/**
 * @type {AssertionUtilities['bare']}
 */
const bare = (text, spaces = undefined) => {
  if (typeof text !== 'string' || !regexpExec(canBeBare, text)) {
    return quote(text, spaces);
  }
  const result = freeze({
    toString: freeze(() => text),
  });
  weakmapSet(declassifiers, result, text);
  return result;
};$h͏_once.bare(bare);
freeze(bare);

// /////////////////////////////////////////////////////////////////////////////

/**
 * @typedef {{ template: TemplateStringsArray | string[], args: any[] }} DetailsParts
 *
 * The contents of a `details` template literal tag: literal strings (always at
 * least one) and arbitrary substitution values from in between them.
 *
 * Unquoted substitution values are sensitive (and are redacted in error
 * `message` strings), so a DetailsPart must not leak outside of this file.
 */

/**
 * Maps the result of a `details` tagged template literal back to a record of
 * that template literal's contents.
 *
 * @type {WeakMap<DetailsToken, DetailsParts>}
 */
const hiddenDetailsMap = new WeakMap();

/**
 * Construct an error message string from `details` template literal contents,
 * replacing unquoted substitution values with redactions.
 *
 * @param {DetailsParts} hiddenDetails
 * @returns {string}
 */
const getMessageString = ({ template, args }) => {
  const parts = [template[0]];
  for (let i = 0; i < args.length; i += 1) {
    const arg = args[i];
    let argStr;
    if (weakmapHas(declassifiers, arg)) {
      argStr = `${arg}`;
    } else if (isError(arg)) {
      argStr = `(${an(arg.name)})`;
    } else {
      argStr = `(${an(typeof arg)})`;
    }
    arrayPush(parts, argStr, template[i + 1]);
  }
  return arrayJoin(parts, '');
};

/**
 * Define `toString` behavior for DetailsToken. To minimize the overhead of
 * creating new instances, we do this with an inherited `this`-sensitive method,
 * even though we normally avoid such sensitivity. To protect the method from
 * inappropriate application, it verifies that `this` is registered in
 * `redactedDetails` before doing interesting work.
 *
 * The behavior must not reveal anything redacted, so we use `getMessageString`
 * to return the same value as the message for a thrown assertion-failure error.
 */
const DetailsTokenProto = freeze({
  toString() {
    const hiddenDetails = weakmapGet(hiddenDetailsMap, this);
    if (hiddenDetails === undefined) {
      return '[Not a DetailsToken]';
    }
    return getMessageString(hiddenDetails);
  },
});
freeze(DetailsTokenProto.toString);

/**
 * Normally this is the function exported as `assert.details` and often
 * spelled `X`. However, if the `{errorTaming: 'unsafe'}` or
 * `{errorTaming: 'unsafe-debug'}` option is
 * given to `lockdown`, then `unredactedDetails` is used instead.
 *
 * There are some unconditional uses of `redactedDetails` in this module. All
 * of them should be uses where the template literal has no redacted (unquoted)
 * substitution values. In those cases, `redactedDetails` is equivalent to
 * `unredactedDetails`.
 *
 * @type {AssertionUtilities['details']}
 */
const redactedDetails = (template, ...args) => {
  // In case the result of this call is never used, perform as little processing
  // as possible here to keep things fast.
  const detailsToken = freeze({ __proto__: DetailsTokenProto });
  weakmapSet(hiddenDetailsMap, detailsToken, { template, args });
  return /** @type {DetailsToken} */ (/** @type {unknown} */ (detailsToken));
};$h͏_once.redactedDetails(redactedDetails);
freeze(redactedDetails);

/**
 * `unredactedDetails` is like `details` except that it does not redact
 * anything. It acts like `details` would act if all substitution values
 * were wrapped with the `quote` function above (the function normally
 * spelled `q`). If the `{errorTaming: 'unsafe'}`
 * or `{errorTaming: 'unsafe-debug'}` option is given to
 * `lockdown`, then the lockdown-shim arranges for the global `assert` to be
 * one whose `details` property is `unredactedDetails`.
 * This setting optimizes the debugging and testing experience at the price
 * of safety. `unredactedDetails` also sacrifices the speed of `details`,
 * which is usually fine in debugging and testing.
 *
 * @type {AssertionUtilities['details']}
 */
const unredactedDetails = (template, ...args) => {
  args = arrayMap(args, arg =>
    weakmapHas(declassifiers, arg) ? arg : quote(arg),
  );
  return redactedDetails(template, ...args);
};$h͏_once.unredactedDetails(unredactedDetails);
freeze(unredactedDetails);


const leadingSpacePattern = sealRegexp(/^ /);
const trailingSpacePattern = sealRegexp(/ $/);

/**
 * Get arguments suitable for a console logger function (e.g., `console.error`)
 * from `details` template literal contents, unquoting quoted substitution
 * values.
 *
 * @param {DetailsParts} hiddenDetails
 * @returns {LogArgs}
 */
const getLogArgs = ({ template, args }) => {
  const logArgs = [template[0]];
  for (let i = 0; i < args.length; i += 1) {
    let arg = args[i];
    if (weakmapHas(declassifiers, arg)) {
      arg = weakmapGet(declassifiers, arg);
    }
    // Remove substitution-adjacent spaces from template fixed-string parts
    // (since console logging inserts its own argument-separating spaces).
    const prevLiteralPart = regexpReplace(
      trailingSpacePattern,
      arrayPop(logArgs) || '',
      '',
    );
    if (prevLiteralPart !== '') {
      arrayPush(logArgs, prevLiteralPart);
    }
    const nextLiteralPart = regexpReplace(
      leadingSpacePattern,
      template[i + 1],
      '',
    );
    arrayPush(logArgs, arg, nextLiteralPart);
  }
  if (logArgs[logArgs.length - 1] === '') {
    arrayPop(logArgs);
  }
  return logArgs;
};

/**
 * Maps from an error object to arguments suitable for a privileged console
 * logger function such as `console.error`, including values that may be
 * redacted in the error's `message`.
 *
 * @type {WeakMap<Error, LogArgs>}
 */
const hiddenMessageLogArgs = new WeakMap();

// So each error tag will be unique.
let errorTagNum = 0;

/**
 * @type {WeakMap<Error, string>}
 */
const errorTags = new WeakMap();

/**
 * @param {Error} err
 * @param {string=} optErrorName
 * @returns {string}
 */
const tagError = (err, optErrorName = err.name) => {
  let errorTag = weakmapGet(errorTags, err);
  if (errorTag !== undefined) {
    return errorTag;
  }
  errorTagNum += 1;
  errorTag = `${optErrorName}#${errorTagNum}`;
  weakmapSet(errorTags, err, errorTag);
  return errorTag;
};

/**
 * Make reasonable best efforts to make a `Passable` error.
 *   - `sanitizeError` will remove any "extraneous" own properties already added
 *     by the host,
 *     such as `fileName`,`lineNumber` on FireFox or `line` on Safari.
 *   - If any such "extraneous" properties were removed, `sanitizeError` will
 *     annotate
 *     the error with them, so they still appear on the causal console
 *     log output for diagnostic purposes, but not be otherwise visible.
 *   - `sanitizeError` will ensure that any expected properties already
 *     added by the host are data
 *     properties, converting accessor properties to data properties as needed,
 *     such as `stack` on v8 (Chrome, Brave, Edge?)
 *   - `sanitizeError` will freeze the error, preventing any correct engine from
 *     adding or
 *     altering any of the error's own properties `sanitizeError` is done.
 *
 * However, `sanitizeError` will not, for example, `harden`
 * (i.e., deeply freeze)
 * or ensure that the `cause` or `errors` property satisfy the `Passable`
 * constraints. The purpose of `sanitizeError` is only to protect against
 * mischief the host may have already added to the error as created,
 * not to ensure that the error is actually Passable. For that,
 * see `toPassableError` in `@endo/pass-style`.
 *
 * @param {Error} error
 */
       const sanitizeError = error => {
  const descs = getOwnPropertyDescriptors(error);
  const {
    name: _nameDesc,
    message: _messageDesc,
    errors: _errorsDesc = undefined,
    cause: _causeDesc = undefined,
    stack: _stackDesc = undefined,
    ...restDescs
  } = descs;

  const restNames = ownKeys(restDescs);
  if (restNames.length >= 1) {
    for (const name of restNames) {
      delete error[name];
    }
    const dropped = create(objectPrototype, restDescs);
    const droppedDetails = redactedDetails`originally with properties ${quote(dropped)}`;
    // eslint-disable-next-line no-use-before-define
    note(error, droppedDetails);
  }
  for (const name of ownKeys(error)) {
    // @ts-expect-error TypeScript is still confused by symbols as property keys
    const desc = descs[name];
    if (desc && hasOwn(desc, 'get')) {
      const value = error[name]; // invokes the getter
      defineProperty(error, name, { value });
    }
  }
  freeze(error);
};

/**
 * @type {AssertionUtilities['makeError']}
 */$h͏_once.sanitizeError(sanitizeError);
const makeError = (
  optDetails = redactedDetails`Assert failed`,
  errConstructor = globalThis.Error,
  {
    errorName = undefined,
    cause = undefined,
    errors = undefined,
    sanitize = true,
  } = {},
) => {
  // Promote string-valued `optDetails` into a minimal DetailsParts
  // consisting of that string as the sole literal part with no substitutions.
  if (typeof optDetails === 'string') {
    optDetails = redactedDetails([optDetails]);
  }
  const hiddenDetails = weakmapGet(hiddenDetailsMap, optDetails);
  if (hiddenDetails === undefined) {
    throw TypeError(`unrecognized details ${quote(optDetails)}`);
  }
  const messageString = getMessageString(hiddenDetails);
  const opts = cause && { cause };
  let error;
  if (
    typeof AggregateError !== 'undefined' &&
    errConstructor === AggregateError
  ) {
    error = AggregateError(errors || [], messageString, opts);
  } else {
    const ErrorCtor = /** @type {ErrorConstructor} */ (errConstructor);
    error = ErrorCtor(messageString, opts);
    // Since we need to tolerate `errors` on an AggregateError, we may as well
    // tolerate it on all errors.
    if (errors !== undefined) {
      defineProperty(error, 'errors', {
        value: errors,
        writable: true,
        enumerable: false,
        configurable: true,
      });
    }
  }
  weakmapSet(hiddenMessageLogArgs, error, getLogArgs(hiddenDetails));
  if (errorName !== undefined) {
    tagError(error, errorName);
  }
  if (sanitize) {
    sanitizeError(error);
  }
  // The next line is a particularly fruitful place to put a breakpoint.
  return error;
};$h͏_once.makeError(makeError);
freeze(makeError);

// /////////////////////////////////////////////////////////////////////////////

const { addLogArgs: addNoteLogArgs, takeLogArgsArray: takeAllNoteLogArgs } =
  makeNoteLogArgsArrayKit();

/**
 * An augmented console will normally only take the hidden noteArgs array once,
 * when it logs the error being annotated. Once that happens, further
 * annotations of that error should go to the console immediately. We arrange
 * that by accepting a note-callback function from the console as an optional
 * part of that taking operation. Normally there will only be at most one
 * callback per error, but that depends on console behavior which we should not
 * assume. We make this an array of callbacks so multiple registrations
 * are independent.
 *
 * @type {WeakMap<Error, NoteCallback[]>}
 */
const hiddenNoteCallbacks = new WeakMap();

/** @type {AssertionUtilities['note']} */
const note = (error, detailsNote) => {
  // Promote string-valued `detailsNote` into a minimal DetailsParts consisting
  // of that string as the sole literal part with no substitutions.
  if (typeof detailsNote === 'string') {
    detailsNote = redactedDetails([detailsNote]);
  }
  const hiddenDetails = weakmapGet(hiddenDetailsMap, detailsNote);
  if (hiddenDetails === undefined) {
    throw TypeError(`unrecognized details ${quote(detailsNote)}`);
  }
  const logArgs = getLogArgs(hiddenDetails);
  const callbacks = weakmapGet(hiddenNoteCallbacks, error);
  if (callbacks !== undefined) {
    for (const callback of callbacks) {
      callback(error, logArgs);
    }
  } else {
    addNoteLogArgs(error, logArgs);
  }
};$h͏_once.note(note);
freeze(note);

/**
 * The unprivileged form that just uses the de facto `error.stack` property.
 * The start compartment normally has a privileged `globalThis.getStackString`
 * which should be preferred if present.
 *
 * @param {Error} error
 * @returns {string}
 */
const defaultGetStackString = error => {
  if (!('stack' in error)) {
    return '';
  }
  const stackString = `${error.stack}`;
  const pos = stringIndexOf(stackString, '\n');
  if (stringStartsWith(stackString, ' ') || pos === -1) {
    return stackString;
  }
  return stringSlice(stackString, pos + 1); // exclude the initial newline
};

/** @type {LoggedErrorHandler} */
const loggedErrorHandler = {
  getStackString: globalThis.getStackString || defaultGetStackString,
  tagError: error => tagError(error),
  resetErrorTagNum: () => {
    errorTagNum = 0;
  },
  getMessageLogArgs: error => weakmapGet(hiddenMessageLogArgs, error),
  takeMessageLogArgs: error => {
    const logArgs = weakmapGet(hiddenMessageLogArgs, error);
    weakmapDelete(hiddenMessageLogArgs, error);
    return logArgs;
  },
  takeNoteLogArgsArray: (error, callback) => {
    const logArgsArray = takeAllNoteLogArgs(error);
    if (callback !== undefined) {
      const callbacks = weakmapGet(hiddenNoteCallbacks, error);
      if (callbacks) {
        arrayPush(callbacks, callback);
      } else {
        weakmapSet(hiddenNoteCallbacks, error, [callback]);
      }
    }
    return logArgsArray || [];
  },
};$h͏_once.loggedErrorHandler(loggedErrorHandler);
freeze(loggedErrorHandler);


// /////////////////////////////////////////////////////////////////////////////

/**
 * @type {MakeAssert}
 */
       const makeAssert = (optRaise = undefined, unredacted = false) => {
  const details = unredacted ? unredactedDetails : redactedDetails;
  const assertFailedDetails = details`Check failed`;

  /** @type {AssertionFunctions['fail']} */
  const fail = (
    optDetails = assertFailedDetails,
    errConstructor = undefined,
    options = undefined,
  ) => {
    const reason = makeError(optDetails, errConstructor, options);
    if (optRaise !== undefined) {
      optRaise(reason);
    }
    throw reason;
  };
  freeze(fail);

  /** @type {AssertionUtilities['Fail']} */
  const Fail = (template, ...args) => fail(details(template, ...args));

  // Don't freeze or export `assert` until we add methods.
  /** @type {BaseAssert} */
  const assert = (
    condition,
    optDetails = undefined,
    errConstructor = undefined,
    options = undefined,
  ) => {
    condition || fail(optDetails, errConstructor, options);
  };

  /** @type {AssertionFunctions['equal']} */
  const equal = (
    actual,
    expected,
    optDetails = undefined,
    errConstructor = undefined,
    options = undefined,
  ) => {
    is(actual, expected) ||
      fail(
        optDetails || details`Expected ${actual} is same as ${expected}`,
        errConstructor || RangeError,
        options,
      );
  };
  freeze(equal);

  /** @type {AssertionFunctions['typeof']} */
  const assertTypeof = (specimen, typename, optDetails) => {
    // This will safely fall through if typename is not a string,
    // which is what we want.
    // eslint-disable-next-line valid-typeof
    if (typeof specimen === typename) {
      return;
    }
    typeof typename === 'string' || Fail`${quote(typename)} must be a string`;

    if (optDetails === undefined) {
      // Embed the type phrase without quotes.
      const typeWithDeterminer = an(typename);
      optDetails = details`${specimen} must be ${bare(typeWithDeterminer)}`;
    }
    fail(optDetails, TypeError);
  };
  freeze(assertTypeof);

  /** @type {AssertionFunctions['string']} */
  const assertString = (specimen, optDetails = undefined) =>
    assertTypeof(specimen, 'string', optDetails);

  /** @type {Pick<AssertionFunctions, keyof AssertionFunctions>} */
  const assertionFunctions = {
    equal,
    typeof: assertTypeof,
    string: assertString,
    fail,
  };

  /** @type {AssertionUtilities} */
  const assertionUtilities = {
    makeError,
    note,
    details,
    Fail,
    quote,
    bare,
  };

  /** @type {DeprecatedAssertionUtilities} */
  const deprecated = { error: makeError, makeAssert };

  /** @type {Assert} */
  const finishedAssert = assign(assert, {
    ...assertionFunctions,
    ...assertionUtilities,
    ...deprecated,
  });
  return freeze(finishedAssert);
};$h͏_once.makeAssert(makeAssert);
freeze(makeAssert);

/** @type {Assert} */
const assert = makeAssert();$h͏_once.assert(assert);


// Internal, to obviate polymorphic dispatch, but may become rigorously
// consistent with @endo/error:

/** @type {AssertionFunctions['equal']} */
const assertEqual = assert.equal;$h͏_once.assertEqual(assertEqual);
})()
,
// === 14. ses ./src/make-hardener.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Set,String,TypeError,WeakSet,globalThis,apply,arrayForEach,defineProperty,freeze,getOwnPropertyDescriptor,getOwnPropertyDescriptors,getPrototypeOf,isInteger,isPrimitive,hasOwn,ownKeys,preventExtensions,setAdd,setForEach,setHas,toStringTagSymbol,typedArrayPrototype,weaksetAdd,weaksetHas,FERAL_STACK_GETTER,FERAL_STACK_SETTER,isError,assert;$h͏_imports([["./commons.js", [["Set",[$h͏_a => (Set = $h͏_a)]],["String",[$h͏_a => (String = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["WeakSet",[$h͏_a => (WeakSet = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["apply",[$h͏_a => (apply = $h͏_a)]],["arrayForEach",[$h͏_a => (arrayForEach = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]],["getPrototypeOf",[$h͏_a => (getPrototypeOf = $h͏_a)]],["isInteger",[$h͏_a => (isInteger = $h͏_a)]],["isPrimitive",[$h͏_a => (isPrimitive = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]],["ownKeys",[$h͏_a => (ownKeys = $h͏_a)]],["preventExtensions",[$h͏_a => (preventExtensions = $h͏_a)]],["setAdd",[$h͏_a => (setAdd = $h͏_a)]],["setForEach",[$h͏_a => (setForEach = $h͏_a)]],["setHas",[$h͏_a => (setHas = $h͏_a)]],["toStringTagSymbol",[$h͏_a => (toStringTagSymbol = $h͏_a)]],["typedArrayPrototype",[$h͏_a => (typedArrayPrototype = $h͏_a)]],["weaksetAdd",[$h͏_a => (weaksetAdd = $h͏_a)]],["weaksetHas",[$h͏_a => (weaksetHas = $h͏_a)]],["FERAL_STACK_GETTER",[$h͏_a => (FERAL_STACK_GETTER = $h͏_a)]],["FERAL_STACK_SETTER",[$h͏_a => (FERAL_STACK_SETTER = $h͏_a)]],["isError",[$h͏_a => (isError = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);





















































/**
 * @import {Harden} from '../types.js'
 */

// Obtain the string tag accessor of of TypedArray so we can indirectly use the
// TypedArray brand check it employs.
const typedArrayToStringTag = getOwnPropertyDescriptor(
  typedArrayPrototype,
  toStringTagSymbol,
);
assert(typedArrayToStringTag);
const getTypedArrayToStringTag = typedArrayToStringTag.get;
assert(getTypedArrayToStringTag);

// Exported for tests.
/**
 * Duplicates packages/marshal/src/helpers/passStyle-helpers.js to avoid a dependency.
 *
 * @param {unknown} object
 */
       const isTypedArray = object => {
  // The object must pass a brand check or toStringTag will return undefined.
  const tag = apply(getTypedArrayToStringTag, object, []);
  return tag !== undefined;
};

/**
 * Tests if a property key is an integer-valued canonical numeric index.
 * https://tc39.es/ecma262/#sec-canonicalnumericindexstring
 *
 * @param {string | symbol} propertyKey
 */$h͏_once.isTypedArray(isTypedArray);
const isCanonicalIntegerIndexString = propertyKey => {
  const n = +String(propertyKey);
  return isInteger(n) && String(n) === propertyKey;
};

/**
 * @template T
 * @param {ArrayLike<T>} array
 */
const freezeTypedArray = array => {
  preventExtensions(array);

  // Downgrade writable expandos to readonly, even if non-configurable.
  // We get each descriptor individually rather than using
  // getOwnPropertyDescriptors in order to fail safe when encountering
  // an obscure GraalJS issue where getOwnPropertyDescriptor returns
  // undefined for a property that does exist.
  arrayForEach(ownKeys(array), (/** @type {string | symbol} */ name) => {
    const desc = getOwnPropertyDescriptor(array, name);
    assert(desc);
    // TypedArrays are integer-indexed exotic objects, which define special
    // treatment for property names in canonical numeric form:
    // integers in range are permanently writable and non-configurable.
    // https://tc39.es/ecma262/#sec-integer-indexed-exotic-objects
    //
    // This is analogous to the data of a hardened Map or Set,
    // so we carve out this exceptional behavior but make all other
    // properties non-configurable.
    if (!isCanonicalIntegerIndexString(name)) {
      defineProperty(array, name, {
        ...desc,
        writable: false,
        configurable: false,
      });
    }
  });
};

/**
 * Create a `harden` function.
 *
 * @returns {Harden}
 */
       const makeHardener = () => {
  // Use a native hardener if possible.
  if (typeof globalThis.harden === 'function') {
    const safeHarden = globalThis.harden;
    return safeHarden;
  }

  const hardened = new WeakSet();

  const { harden } = {
    /**
     * @template T
     * @param {T} root
     * @returns {T}
     */
    harden(root) {
      const toFreeze = new Set();

      // If val is something we should be freezing but aren't yet,
      // add it to toFreeze.
      /**
       * @param {any} val
       */
      function enqueue(val) {
        if (isPrimitive(val)) {
          // ignore primitives
          return;
        }
        const type = typeof val;
        if (type !== 'object' && type !== 'function') {
          // future proof: break until someone figures out what it should do
          throw TypeError(`Unexpected typeof: ${type}`);
        }
        if (weaksetHas(hardened, val) || setHas(toFreeze, val)) {
          // Ignore if this is an exit, or we've already visited it
          return;
        }
        // console.warn(`adding ${val} to toFreeze`, val);
        setAdd(toFreeze, val);
      }

      /**
       * @param {any} obj
       */
      const baseFreezeAndTraverse = obj => {
        // Now freeze the object to ensure reactive
        // objects such as proxies won't add properties
        // during traversal, before they get frozen.

        // Object are verified before being enqueued,
        // therefore this is a valid candidate.
        // Throws if this fails (strict mode).
        // Also throws if the object is an ArrayBuffer or any TypedArray.
        if (isTypedArray(obj)) {
          freezeTypedArray(obj);
        } else {
          freeze(obj);
        }

        // we rely upon certain commitments of Object.freeze and proxies here

        // get stable/immutable outbound links before a Proxy has a chance to do
        // something sneaky.
        const descs = getOwnPropertyDescriptors(obj);
        const proto = getPrototypeOf(obj);
        enqueue(proto);

        arrayForEach(ownKeys(descs), (/** @type {string | symbol} */ name) => {
          // The 'name' may be a symbol, and TypeScript doesn't like us to
          // index arbitrary symbols on objects, so we pretend they're just
          // strings.
          const desc = descs[/** @type {string} */ (name)];
          // getOwnPropertyDescriptors is guaranteed to return well-formed
          // descriptors, but they still inherit from Object.prototype. If
          // someone has poisoned Object.prototype to add 'value' or 'get'
          // properties, then a simple 'if ("value" in desc)' or 'desc.value'
          // test could be confused. We use hasOwnProperty to be sure about
          // whether 'value' is present or not, which tells us for sure that
          // this is a data property.
          if (hasOwn(desc, 'value')) {
            enqueue(desc.value);
          } else {
            enqueue(desc.get);
            enqueue(desc.set);
          }
        });
      };

      const freezeAndTraverse =
        FERAL_STACK_GETTER === undefined && FERAL_STACK_SETTER === undefined
          ? // On platforms without v8's error own stack accessor problem,
            // don't pay for any extra overhead.
            baseFreezeAndTraverse
          : obj => {
              if (isError(obj)) {
                // Only pay the overhead if it first passes this cheap isError
                // check. Otherwise, it will be unrepaired, but won't be judged
                // to be a passable error anyway, so will not be unsafe.
                const stackDesc = getOwnPropertyDescriptor(obj, 'stack');
                if (
                  stackDesc &&
                  stackDesc.get === FERAL_STACK_GETTER &&
                  stackDesc.configurable
                ) {
                  // Can only repair if it is configurable. Otherwise, leave
                  // unrepaired, in which case it will not be judged passable,
                  // avoiding a safety problem.
                  defineProperty(obj, 'stack', {
                    // NOTE: Calls getter during harden, which seems dangerous.
                    // But we're only calling the problematic getter whose
                    // hazards we think we understand.
                    // @ts-expect-error TS should know FERAL_STACK_GETTER
                    // cannot be `undefined` here.
                    // See https://github.com/endojs/endo/pull/2232#discussion_r1575179471
                    value: apply(FERAL_STACK_GETTER, obj, []),
                  });
                }
              }
              return baseFreezeAndTraverse(obj);
            };

      const dequeue = () => {
        // New values added before forEach() has finished will be visited.
        setForEach(toFreeze, freezeAndTraverse);
      };

      /** @param {any} value */
      const markHardened = value => {
        weaksetAdd(hardened, value);
      };

      const commit = () => {
        setForEach(toFreeze, markHardened);
      };

      enqueue(root);
      dequeue();
      // console.warn("toFreeze set:", toFreeze);
      commit();

      return root;
    },
  };

  return harden;
};$h͏_once.makeHardener(makeHardener);
})()
,
// === 15. ses ./src/cauterize-property.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let hasOwn;$h͏_imports([["./commons.js", [["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]]]]]);

/**
 * @import {Reporter} from './reporting-types.js'
 */

/**
 * Delete `obj[prop]` or at least make it harmless.
 *
 * If the property was not expected, then emit a reporter-dependent warning
 * to bring attention to this case, so someone can determine what to do with it.
 *
 * If the property to be deleted is a function's `.prototype` property, this
 * will normally be because the function was supposed to be a
 * - builtin method or non-constructor function
 * - arrow function
 * - concise method
 *
 * all of whom are not supposed to have a `.prototype` property. Nevertheless,
 * on some platforms (like older versions of Hermes), or as a result of
 * some shim-based mods to the primordials (like core-js?), some of these
 * functions may accidentally be more like `function` functions with
 * an undeletable `.prototype` property. In these cases, if we can
 * set the value of that bogus `.prototype` property to `undefined`,
 * we do so, issuing a warning, rather than failing to initialize ses.
 *
 * @param {object} obj
 * @param {PropertyKey} prop
 * @param {boolean} known If deletion is expected, don't warn
 * @param {string} subPath Used for warning messages
 * @param {Reporter} reporter Where to issue warning or error.
 * @returns {void}
 */
       const cauterizeProperty = (
  obj,
  prop,
  known,
  subPath,
  { warn, error },
) => {
  // Either the object lacks a permit or the object doesn't match the
  // permit.
  // If the permit is specifically false, not merely undefined,
  // this is a property we expect to see because we know it exists in
  // some environments and we have expressly decided to exclude it.
  // Any other disallowed property is one we have not audited and we log
  // that we are removing it so we know to look into it, as happens when
  // the language evolves new features to existing intrinsics.
  if (!known) {
    warn(`Removing ${subPath}`);
  }
  try {
    delete obj[prop];
  } catch (err) {
    if (hasOwn(obj, prop)) {
      if (typeof obj === 'function' && prop === 'prototype') {
        obj.prototype = undefined;
        if (obj.prototype === undefined) {
          warn(`Tolerating undeletable ${subPath} === undefined`);
          return;
        }
      }
      error(`failed to delete ${subPath}`, err);
    } else {
      error(`deleting ${subPath} threw`, err);
    }
    throw err;
  }
};$h͏_once.cauterizeProperty(cauterizeProperty);
})()
,
// === 16. ses ./src/permits.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let arrayPush,arrayForEach;$h͏_imports([["./commons.js", [["arrayPush",[$h͏_a => (arrayPush = $h͏_a)]],["arrayForEach",[$h͏_a => (arrayForEach = $h͏_a)]]]]]);




/** @import {GenericErrorConstructor} from '../types.js' */

/**
 * Exports {@code permits}, a recursively defined
 * JSON record enumerating all intrinsics and their properties
 * according to ECMA specs.
 *
 * @author JF Paradis
 * @author Mark S. Miller
 *
 * @module
 */

/**
 * constantProperties
 * non-configurable, non-writable data properties of all global objects.
 * Must be powerless.
 * Maps from property name to the actual value
 */
       const constantProperties = {
  // *** Value Properties of the Global Object

  Infinity,
  NaN,
  undefined,
};

/**
 * universalPropertyNames
 * Properties of all global objects.
 * Must be powerless.
 * Maps from property name to the intrinsic name in the permits.
 */$h͏_once.constantProperties(constantProperties);
       const universalPropertyNames = {
  // *** Function Properties of the Global Object

  isFinite: 'isFinite',
  isNaN: 'isNaN',
  parseFloat: 'parseFloat',
  parseInt: 'parseInt',

  decodeURI: 'decodeURI',
  decodeURIComponent: 'decodeURIComponent',
  encodeURI: 'encodeURI',
  encodeURIComponent: 'encodeURIComponent',

  // *** Constructor Properties of the Global Object

  Array: 'Array',
  ArrayBuffer: 'ArrayBuffer',
  BigInt: 'BigInt',
  BigInt64Array: 'BigInt64Array',
  BigUint64Array: 'BigUint64Array',
  Boolean: 'Boolean',
  DataView: 'DataView',
  EvalError: 'EvalError',
  // https://github.com/tc39/proposal-float16array
  Float16Array: 'Float16Array',
  Float32Array: 'Float32Array',
  Float64Array: 'Float64Array',
  Int8Array: 'Int8Array',
  Int16Array: 'Int16Array',
  Int32Array: 'Int32Array',
  Map: 'Map',
  Number: 'Number',
  Object: 'Object',
  Promise: 'Promise',
  Proxy: 'Proxy',
  RangeError: 'RangeError',
  ReferenceError: 'ReferenceError',
  Set: 'Set',
  String: 'String',
  SyntaxError: 'SyntaxError',
  TypeError: 'TypeError',
  Uint8Array: 'Uint8Array',
  Uint8ClampedArray: 'Uint8ClampedArray',
  Uint16Array: 'Uint16Array',
  Uint32Array: 'Uint32Array',
  URIError: 'URIError',
  WeakMap: 'WeakMap',
  WeakSet: 'WeakSet',
  // https://github.com/tc39/proposal-iterator-helpers
  Iterator: 'Iterator',
  // https://github.com/tc39/proposal-async-iterator-helpers
  AsyncIterator: 'AsyncIterator',
  // https://github.com/endojs/endo/issues/550
  AggregateError: 'AggregateError',

  // https://github.com/tc39/proposal-explicit-resource-management
  // TODO DisposableStack, AsyncDisposableStack
  // DisposableStack: 'DisposableStack',
  // AsyncDisposableStack: 'AsyncDisposableStack',

  // https://tc39.es/proposal-shadowrealm/
  // TODO ShadowRealm
  // ShadowRealm: 'ShadowRealm',

  // *** Other Properties of the Global Object

  JSON: 'JSON',
  Reflect: 'Reflect',

  // *** Annex B

  escape: 'escape',
  unescape: 'unescape',

  // ESNext

  // https://github.com/tc39/proposal-source-phase-imports?tab=readme-ov-file#js-module-source
  ModuleSource: 'ModuleSource',

  lockdown: 'lockdown',
  harden: 'harden',

  HandledPromise: 'HandledPromise'  // TODO: Until Promise.delegate (see below).
};

/**
 * initialGlobalPropertyNames
 * Those found only on the initial global, i.e., the global of the
 * start compartment, as well as any compartments created before lockdown.
 * These may provide much of the power provided by the original.
 * Maps from property name to the intrinsic name in the permits.
 */$h͏_once.universalPropertyNames(universalPropertyNames);
       const initialGlobalPropertyNames = {
  // *** Constructor Properties of the Global Object

  Date: '%InitialDate%',
  Error: '%InitialError%',
  RegExp: '%InitialRegExp%',

  // Omit `Symbol`, because we want the original to appear on the
  // start compartment without passing through the permits mechanism, since
  // we want to preserve all its properties, even if we never heard of them.
  // Symbol: '%InitialSymbol%',

  // *** Other Properties of the Global Object

  Math: '%InitialMath%',

  // ESNext

  // From Error-stack proposal
  // Only on initial global. No corresponding
  // powerless form for other globals.
  getStackString: '%InitialGetStackString%'

  // TODO https://github.com/Agoric/SES-shim/issues/551
  // Need initial WeakRef and FinalizationGroup in
  // start compartment only.

  // TODO Temporal
  // https://github.com/tc39/proposal-temporal
  // Temporal: '%InitialTemporal%' // with Temporal.Now
};

/**
 * sharedGlobalPropertyNames
 * Those found only on the globals of new compartments created after lockdown,
 * which must therefore be powerless.
 * Maps from property name to the intrinsic name in the permits.
 */$h͏_once.initialGlobalPropertyNames(initialGlobalPropertyNames);
       const sharedGlobalPropertyNames = {
  // *** Constructor Properties of the Global Object

  Date: '%SharedDate%',
  Error: '%SharedError%',
  RegExp: '%SharedRegExp%',
  Symbol: '%SharedSymbol%',

  // *** Other Properties of the Global Object

  Math: '%SharedMath%'

  // TODO Temporal
  // https://github.com/tc39/proposal-temporal
  // Temporal: '%SharedTemporal%' // without Temporal.Now
};

/**
 * uniqueGlobalPropertyNames
 * Those made separately for each global, including the initial global
 * of the start compartment.
 * Maps from property name to the intrinsic name in the permits
 * (which is currently always the same).
 */$h͏_once.sharedGlobalPropertyNames(sharedGlobalPropertyNames);
       const uniqueGlobalPropertyNames = {
  // *** Value Properties of the Global Object

  globalThis: '%UniqueGlobalThis%',

  // *** Function Properties of the Global Object

  eval: '%UniqueEval%',

  // *** Constructor Properties of the Global Object

  Function: '%UniqueFunction%',

  // *** Other Properties of the Global Object

  // ESNext

  Compartment: '%UniqueCompartment%'
  // According to current agreements, eventually the Realm constructor too.
  // 'Realm',
};

// All the "subclasses" of Error. These are collectively represented in the
// ECMAScript spec by the meta variable NativeError.
/** @type {GenericErrorConstructor[]} */$h͏_once.uniqueGlobalPropertyNames(uniqueGlobalPropertyNames);
const NativeErrors = [
  EvalError,
  RangeError,
  ReferenceError,
  SyntaxError,
  TypeError,
  URIError
  // https://github.com/endojs/endo/issues/550
  // Commented out to accommodate platforms prior to AggregateError.
  // Instead, conditional push below.
  // AggregateError,
];$h͏_once.NativeErrors(NativeErrors);

if (typeof AggregateError !== 'undefined') {
  // Conditional, to accommodate platforms prior to AggregateError
  arrayPush(NativeErrors, AggregateError);
}



/**
 * <p>Each JSON record enumerates the disposition of the properties on
 *    some corresponding intrinsic object.
 *
 * <p>All records are made of key-value pairs where the key
 *    is the property to process, and the value is the associated
 *    dispositions a.k.a. the "permit". Those permits can be:
 * <ul>
 * <li>The boolean value "false", in which case this property is
 *     blacklisted and simply removed. Properties not mentioned
 *     are also considered blacklisted and are removed.
 * <li>A string value equal to a primitive ("number", "string", etc),
 *     in which case the property is permitted if its value property
 *     is typeof the given type. For example, {@code "Infinity"} leads to
 *     "number" and property values that fail {@code typeof "number"}.
 *     are removed.
 * <li>A string value equal to an intinsic name ("ObjectPrototype",
 *     "Array", etc), in which case the property permitted if its
 *     value property is equal to the value of the corresponfing
 *     intrinsics. For example, {@code Map.prototype} leads to
 *     "MapPrototype" and the property is removed if its value is
 *     not equal to %MapPrototype%
 * <li>Another record, in which case this property is simply
 *     permitted and that next record represents the disposition of
 *     the object which is its value. For example, {@code "Object"}
 *     leads to another record explaining what properties {@code
 *     "Object"} may have and how each such property should be treated.
 *
 * <p>Notes:
 * <li>"[[Proto]]" is used to refer to the "[[Prototype]]" internal
 *     slot, which says which object this object inherits from.
 * <li>"--proto--" is used to refer to the "__proto__" property name,
 *     which is the name of an accessor property on Object.prototype.
 *     In practice, it is used to access the [[Proto]] internal slot,
 *     but is distinct from the internal slot itself. We use
 *     "--proto--" rather than "__proto__" below because "__proto__"
 *     in an object literal is special syntax rather than a normal
 *     property definition.
 * <li>"ObjectPrototype" is the default "[[Proto]]" (when not specified).
 * <li>Constants "fn" and "getter" are used to keep the structure DRY.
 * <li>Symbol properties are listed as follow:
 *     <li>Well-known symbols use the "@@name" form.
 *     <li>Registered symbols use the "RegisteredSymbol(key)" form.
 *     <li>Unique symbols use the "UniqueSymbol(description)" form.
 */

// Function Instances
       const FunctionInstance = {
  '[[Proto]]': '%FunctionPrototype%',
  length: 'number',
  name: 'string'
  // Do not specify "prototype" here, since only Function instances that can
  // be used as a constructor have a prototype property. For constructors,
  // since prototype properties are instance-specific, we define it there.
};

// AsyncFunction Instances
$h͏_once.FunctionInstance(FunctionInstance);const AsyncFunctionInstance={
  // This property is not mentioned in ECMA 262, but is present in V8 and
  // necessary for lockdown to succeed.
  '[[Proto]]': '%AsyncFunctionPrototype%',
};

// Aliases
$h͏_once.AsyncFunctionInstance(AsyncFunctionInstance);const fn=FunctionInstance;
const asyncFn = AsyncFunctionInstance;

const getter = {
  get: fn,
  set: 'undefined',
};

// Possible but not encountered in the specs
// export const setter = {
//   get: 'undefined',
//   set: fn,
// };

const accessor = {
  get: fn,
  set: fn,
};

// eslint-disable-next-line func-names
const strict = function () {
  'use strict';
};

// TODO Remove this once we no longer support the Hermes that needed this.
arrayForEach(['caller', 'arguments'], prop => {
  try {
    strict[prop];
  } catch (e) {
    // https://github.com/facebook/hermes/blob/main/test/hermes/function-non-strict.js
    if (e.message === 'Restricted in strict mode') {
      // Fixed in Static Hermes: https://github.com/facebook/hermes/issues/1582
      FunctionInstance[prop] = accessor;
    }
  }
});

       const isAccessorPermit = permit => {
  return permit === getter || permit === accessor;
};

// NativeError Object Structure
$h͏_once.isAccessorPermit(isAccessorPermit);function NativeError(prototype){
  return {
    // Properties of the NativeError Constructors
    '[[Proto]]': '%SharedError%',

    // NativeError.prototype
    prototype,
  };
}

function NativeErrorPrototype(constructor) {
  return {
    // Properties of the NativeError Prototype Objects
    '[[Proto]]': '%ErrorPrototype%',
    constructor,
    message: 'string',
    name: 'string',
    // Redundantly present only on v8. Safe to remove.
    toString: false,
    // Superfluously present in some versions of V8.
    // https://github.com/tc39/notes/blob/master/meetings/2021-10/oct-26.md#:~:text=However%2C%20Chrome%2093,and%20node%2016.11.
    cause: false,
  };
}

// The TypedArray Constructors
function TypedArray(prototype) {
  return {
    // Properties of the TypedArray Constructors
    '[[Proto]]': '%TypedArray%',
    BYTES_PER_ELEMENT: 'number',
    prototype,
  };
}

function TypedArrayPrototype(constructor) {
  return {
    // Properties of the TypedArray Prototype Objects
    '[[Proto]]': '%TypedArrayPrototype%',
    BYTES_PER_ELEMENT: 'number',
    constructor,
  };
}

// Without Math.random
const CommonMath = {
  E: 'number',
  LN10: 'number',
  LN2: 'number',
  LOG10E: 'number',
  LOG2E: 'number',
  PI: 'number',
  SQRT1_2: 'number',
  SQRT2: 'number',
  '@@toStringTag': 'string',
  abs: fn,
  acos: fn,
  acosh: fn,
  asin: fn,
  asinh: fn,
  atan: fn,
  atanh: fn,
  atan2: fn,
  cbrt: fn,
  ceil: fn,
  clz32: fn,
  cos: fn,
  cosh: fn,
  exp: fn,
  expm1: fn,
  floor: fn,
  fround: fn,
  hypot: fn,
  imul: fn,
  log: fn,
  log1p: fn,
  log10: fn,
  log2: fn,
  max: fn,
  min: fn,
  pow: fn,
  round: fn,
  sign: fn,
  sin: fn,
  sinh: fn,
  sqrt: fn,
  tan: fn,
  tanh: fn,
  trunc: fn,
  // https://github.com/tc39/proposal-float16array
  f16round: fn,
  // https://github.com/tc39/proposal-math-sum
  sumPrecise: fn,

  // See https://github.com/Moddable-OpenSource/moddable/issues/523
  idiv: false,
  // See https://github.com/Moddable-OpenSource/moddable/issues/523
  idivmod: false,
  // See https://github.com/Moddable-OpenSource/moddable/issues/523
  imod: false,
  // See https://github.com/Moddable-OpenSource/moddable/issues/523
  imuldiv: false,
  // See https://github.com/Moddable-OpenSource/moddable/issues/523
  irem: false,
  // See https://github.com/Moddable-OpenSource/moddable/issues/523
  mod: false,
  // See https://github.com/Moddable-OpenSource/moddable/issues/523#issuecomment-1942904505
  irandom: false,
};

       const permitted = {
  // ECMA https://tc39.es/ecma262

  // The intrinsics object has no prototype to avoid conflicts.
  '[[Proto]]': null,

  // %ThrowTypeError%
  '%ThrowTypeError%': fn,

  // *** The Global Object

  // *** Value Properties of the Global Object
  Infinity: 'number',
  NaN: 'number',
  undefined: 'undefined',

  // *** Function Properties of the Global Object

  // eval
  '%UniqueEval%': fn,
  isFinite: fn,
  isNaN: fn,
  parseFloat: fn,
  parseInt: fn,
  decodeURI: fn,
  decodeURIComponent: fn,
  encodeURI: fn,
  encodeURIComponent: fn,

  // *** Fundamental Objects

  Object: {
    // Properties of the Object Constructor
    '[[Proto]]': '%FunctionPrototype%',
    assign: fn,
    create: fn,
    defineProperties: fn,
    defineProperty: fn,
    entries: fn,
    freeze: fn,
    fromEntries: fn,
    getOwnPropertyDescriptor: fn,
    getOwnPropertyDescriptors: fn,
    getOwnPropertyNames: fn,
    getOwnPropertySymbols: fn,
    getPrototypeOf: fn,
    is: fn,
    isExtensible: fn,
    isFrozen: fn,
    isSealed: fn,
    keys: fn,
    preventExtensions: fn,
    prototype: '%ObjectPrototype%',
    seal: fn,
    setPrototypeOf: fn,
    values: fn,
    'RegisteredSymbol(harden)': {
      ...fn,
      // Installed with hardenTaming: 'unsafe'
      isFake: 'boolean',
    },
    // https://github.com/tc39/proposal-accessible-object-hasownproperty
    hasOwn: fn,
    // https://github.com/tc39/proposal-array-grouping
    groupBy: fn,
    // Seen on QuickJS
    __getClass: false,
  },

  '%ObjectPrototype%': {
    // Properties of the Object Prototype Object
    '[[Proto]]': null,
    constructor: 'Object',
    hasOwnProperty: fn,
    isPrototypeOf: fn,
    propertyIsEnumerable: fn,
    toLocaleString: fn,
    toString: fn,
    valueOf: fn,

    // Annex B: Additional Properties of the Object.prototype Object

    // See note in header about the difference between [[Proto]] and --proto--
    // special notations.
    '--proto--': accessor,
    __defineGetter__: fn,
    __defineSetter__: fn,
    __lookupGetter__: fn,
    __lookupSetter__: fn,
  },

  '%UniqueFunction%': {
    // Properties of the Function Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%FunctionPrototype%',
  },

  '%InertFunction%': {
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%FunctionPrototype%',
  },

  '%FunctionPrototype%': {
    apply: fn,
    bind: fn,
    call: fn,
    constructor: '%InertFunction%',
    toString: fn,
    '@@hasInstance': fn,
    // proposed but not yet std. To be removed if there
    caller: false,
    // proposed but not yet std. To be removed if there
    arguments: false,
    // Seen on QuickJS. TODO grab getter for use by console
    fileName: false,
    // Seen on QuickJS. TODO grab getter for use by console
    lineNumber: false,
  },

  Boolean: {
    // Properties of the Boolean Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%BooleanPrototype%',
  },

  '%BooleanPrototype%': {
    constructor: 'Boolean',
    toString: fn,
    valueOf: fn,
  },

  '%SharedSymbol%': {
    // Properties of the Symbol Constructor
    '[[Proto]]': '%FunctionPrototype%',
    asyncIterator: 'symbol',
    for: fn,
    hasInstance: 'symbol',
    isConcatSpreadable: 'symbol',
    iterator: 'symbol',
    keyFor: fn,
    match: 'symbol',
    matchAll: 'symbol',
    prototype: '%SymbolPrototype%',
    replace: 'symbol',
    search: 'symbol',
    species: 'symbol',
    split: 'symbol',
    toPrimitive: 'symbol',
    toStringTag: 'symbol',
    unscopables: 'symbol',
    // https://github.com/tc39/proposal-explicit-resource-management
    asyncDispose: 'symbol',
    // https://github.com/tc39/proposal-explicit-resource-management
    dispose: 'symbol',
    // Seen at core-js https://github.com/zloirock/core-js#ecmascript-symbol
    useSimple: false,
    // Seen at core-js https://github.com/zloirock/core-js#ecmascript-symbol
    useSetter: false,
    // Seen on QuickJS
    operatorSet: false,
  },

  '%SymbolPrototype%': {
    // Properties of the Symbol Prototype Object
    constructor: '%SharedSymbol%',
    description: getter,
    toString: fn,
    valueOf: fn,
    '@@toPrimitive': fn,
    '@@toStringTag': 'string',
  },

  '%InitialError%': {
    // Properties of the Error Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%ErrorPrototype%',
    // Non standard, v8 only, used by tap
    captureStackTrace: fn,
    // Non standard, v8 only, used by tap, tamed to accessor
    stackTraceLimit: accessor,
    // Non standard, v8 only, used by several, tamed to accessor
    prepareStackTrace: accessor,
    // https://github.com/tc39/proposal-is-error
    isError: fn,
  },

  '%SharedError%': {
    // Properties of the Error Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%ErrorPrototype%',
    // Non standard, v8 only, used by tap
    captureStackTrace: fn,
    // Non standard, v8 only, used by tap, tamed to accessor
    stackTraceLimit: accessor,
    // Non standard, v8 only, used by several, tamed to accessor
    prepareStackTrace: accessor,
    // https://github.com/tc39/proposal-is-error
    isError: fn,
  },

  '%ErrorPrototype%': {
    constructor: '%SharedError%',
    message: 'string',
    name: 'string',
    toString: fn,
    // proposed de-facto, assumed TODO
    // Seen on FF Nightly 88.0a1
    at: false,
    // Seen on FF and XS
    stack: accessor,
    // Superfluously present in some versions of V8.
    // https://github.com/tc39/notes/blob/master/meetings/2021-10/oct-26.md#:~:text=However%2C%20Chrome%2093,and%20node%2016.11.
    cause: false,
  },

  // NativeError

  EvalError: NativeError('%EvalErrorPrototype%'),
  RangeError: NativeError('%RangeErrorPrototype%'),
  ReferenceError: NativeError('%ReferenceErrorPrototype%'),
  SyntaxError: NativeError('%SyntaxErrorPrototype%'),
  TypeError: NativeError('%TypeErrorPrototype%'),
  URIError: NativeError('%URIErrorPrototype%'),
  // https://github.com/endojs/endo/issues/550
  AggregateError: NativeError('%AggregateErrorPrototype%'),

  // TODO SuppressedError
  // https://github.com/tc39/proposal-explicit-resource-management
  // SuppressedError: NativeError('%SuppressedErrorPrototype%'),

  '%EvalErrorPrototype%': NativeErrorPrototype('EvalError'),
  '%RangeErrorPrototype%': NativeErrorPrototype('RangeError'),
  '%ReferenceErrorPrototype%': NativeErrorPrototype('ReferenceError'),
  '%SyntaxErrorPrototype%': NativeErrorPrototype('SyntaxError'),
  '%TypeErrorPrototype%': NativeErrorPrototype('TypeError'),
  '%URIErrorPrototype%': NativeErrorPrototype('URIError'),
  // https://github.com/endojs/endo/issues/550
  '%AggregateErrorPrototype%': NativeErrorPrototype('AggregateError'),
  // TODO AggregateError .errors

  // TODO SuppressedError
  // https://github.com/tc39/proposal-explicit-resource-management
  // '%SuppressedErrorPrototype%': NativeErrorPrototype('SuppressedError'),
  // TODO SuppressedError .error
  // TODO SuppressedError .suppressed

  // *** Numbers and Dates

  Number: {
    // Properties of the Number Constructor
    '[[Proto]]': '%FunctionPrototype%',
    EPSILON: 'number',
    isFinite: fn,
    isInteger: fn,
    isNaN: fn,
    isSafeInteger: fn,
    MAX_SAFE_INTEGER: 'number',
    MAX_VALUE: 'number',
    MIN_SAFE_INTEGER: 'number',
    MIN_VALUE: 'number',
    NaN: 'number',
    NEGATIVE_INFINITY: 'number',
    parseFloat: fn,
    parseInt: fn,
    POSITIVE_INFINITY: 'number',
    prototype: '%NumberPrototype%',
  },

  '%NumberPrototype%': {
    // Properties of the Number Prototype Object
    constructor: 'Number',
    toExponential: fn,
    toFixed: fn,
    toLocaleString: fn,
    toPrecision: fn,
    toString: fn,
    valueOf: fn,
  },

  BigInt: {
    // Properties of the BigInt Constructor
    '[[Proto]]': '%FunctionPrototype%',
    asIntN: fn,
    asUintN: fn,
    prototype: '%BigIntPrototype%',
    // See https://github.com/Moddable-OpenSource/moddable/issues/523
    bitLength: false,
    // See https://github.com/Moddable-OpenSource/moddable/issues/523
    fromArrayBuffer: false,
    // Seen on QuickJS
    tdiv: false,
    // Seen on QuickJS
    fdiv: false,
    // Seen on QuickJS
    cdiv: false,
    // Seen on QuickJS
    ediv: false,
    // Seen on QuickJS
    tdivrem: false,
    // Seen on QuickJS
    fdivrem: false,
    // Seen on QuickJS
    cdivrem: false,
    // Seen on QuickJS
    edivrem: false,
    // Seen on QuickJS
    sqrt: false,
    // Seen on QuickJS
    sqrtrem: false,
    // Seen on QuickJS
    floorLog2: false,
    // Seen on QuickJS
    ctz: false,
  },

  '%BigIntPrototype%': {
    constructor: 'BigInt',
    toLocaleString: fn,
    toString: fn,
    valueOf: fn,
    '@@toStringTag': 'string',
  },

  '%InitialMath%': {
    ...CommonMath,
    // `%InitialMath%.random()` has the standard unsafe behavior
    random: fn,
  },

  '%SharedMath%': {
    ...CommonMath,
    // `%SharedMath%.random()` is tamed to always throw
    random: fn,
  },

  '%InitialDate%': {
    // Properties of the Date Constructor
    '[[Proto]]': '%FunctionPrototype%',
    now: fn,
    parse: fn,
    prototype: '%DatePrototype%',
    UTC: fn,
  },

  '%SharedDate%': {
    // Properties of the Date Constructor
    '[[Proto]]': '%FunctionPrototype%',
    // `%SharedDate%.now()` is tamed to always throw
    now: fn,
    parse: fn,
    prototype: '%DatePrototype%',
    UTC: fn,
  },

  '%DatePrototype%': {
    constructor: '%SharedDate%',
    getDate: fn,
    getDay: fn,
    getFullYear: fn,
    getHours: fn,
    getMilliseconds: fn,
    getMinutes: fn,
    getMonth: fn,
    getSeconds: fn,
    getTime: fn,
    getTimezoneOffset: fn,
    getUTCDate: fn,
    getUTCDay: fn,
    getUTCFullYear: fn,
    getUTCHours: fn,
    getUTCMilliseconds: fn,
    getUTCMinutes: fn,
    getUTCMonth: fn,
    getUTCSeconds: fn,
    setDate: fn,
    setFullYear: fn,
    setHours: fn,
    setMilliseconds: fn,
    setMinutes: fn,
    setMonth: fn,
    setSeconds: fn,
    setTime: fn,
    setUTCDate: fn,
    setUTCFullYear: fn,
    setUTCHours: fn,
    setUTCMilliseconds: fn,
    setUTCMinutes: fn,
    setUTCMonth: fn,
    setUTCSeconds: fn,
    toDateString: fn,
    toISOString: fn,
    toJSON: fn,
    toLocaleDateString: fn,
    toLocaleString: fn,
    toLocaleTimeString: fn,
    toString: fn,
    toTimeString: fn,
    toUTCString: fn,
    valueOf: fn,
    '@@toPrimitive': fn,

    // Annex B: Additional Properties of the Date.prototype Object
    getYear: fn,
    setYear: fn,
    toGMTString: fn,
  },

  // Text Processing

  String: {
    // Properties of the String Constructor
    '[[Proto]]': '%FunctionPrototype%',
    fromCharCode: fn,
    fromCodePoint: fn,
    prototype: '%StringPrototype%',
    raw: fn,
    // See https://github.com/Moddable-OpenSource/moddable/issues/523
    fromArrayBuffer: false,
  },

  '%StringPrototype%': {
    // Properties of the String Prototype Object
    length: 'number',
    charAt: fn,
    charCodeAt: fn,
    codePointAt: fn,
    concat: fn,
    constructor: 'String',
    endsWith: fn,
    includes: fn,
    indexOf: fn,
    lastIndexOf: fn,
    localeCompare: fn,
    match: fn,
    matchAll: fn,
    normalize: fn,
    padEnd: fn,
    padStart: fn,
    repeat: fn,
    replace: fn,
    replaceAll: fn, // ES2021
    search: fn,
    slice: fn,
    split: fn,
    startsWith: fn,
    substring: fn,
    toLocaleLowerCase: fn,
    toLocaleUpperCase: fn,
    toLowerCase: fn,
    toString: fn,
    toUpperCase: fn,
    trim: fn,
    trimEnd: fn,
    trimStart: fn,
    valueOf: fn,
    '@@iterator': fn,
    // Failed tc39 proposal
    // https://github.com/tc39/proposal-relative-indexing-method
    at: fn,
    // https://github.com/tc39/proposal-is-usv-string
    isWellFormed: fn,
    toWellFormed: fn,
    unicodeSets: fn,

    // Annex B: Additional Properties of the String.prototype Object
    substr: fn,
    anchor: fn,
    big: fn,
    blink: fn,
    bold: fn,
    fixed: fn,
    fontcolor: fn,
    fontsize: fn,
    italics: fn,
    link: fn,
    small: fn,
    strike: fn,
    sub: fn,
    sup: fn,
    trimLeft: fn,
    trimRight: fn,
    // See https://github.com/Moddable-OpenSource/moddable/issues/523
    compare: false,
    // Seen on QuickJS
    __quote: false,
  },

  '%StringIteratorPrototype%': {
    '[[Proto]]': '%IteratorPrototype%',
    next: fn,
    '@@toStringTag': 'string',
  },

  '%InitialRegExp%': {
    // Properties of the RegExp Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%RegExpPrototype%',
    '@@species': getter,
    // https://github.com/tc39/proposal-regex-escaping
    escape: fn,

    // The https://github.com/tc39/proposal-regexp-legacy-features
    // are all optional, unsafe, and omitted
    input: false,
    $_: false,
    lastMatch: false,
    '$&': false,
    lastParen: false,
    '$+': false,
    leftContext: false,
    '$`': false,
    rightContext: false,
    "$'": false,
    $1: false,
    $2: false,
    $3: false,
    $4: false,
    $5: false,
    $6: false,
    $7: false,
    $8: false,
    $9: false,
  },

  '%SharedRegExp%': {
    // Properties of the RegExp Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%RegExpPrototype%',
    '@@species': getter,
    // https://github.com/tc39/proposal-regex-escaping
    escape: fn,
  },

  '%RegExpPrototype%': {
    // Properties of the RegExp Prototype Object
    constructor: '%SharedRegExp%',
    exec: fn,
    dotAll: getter,
    flags: getter,
    global: getter,
    hasIndices: getter,
    ignoreCase: getter,
    '@@match': fn,
    '@@matchAll': fn,
    multiline: getter,
    '@@replace': fn,
    '@@search': fn,
    source: getter,
    '@@split': fn,
    sticky: getter,
    test: fn,
    toString: fn,
    unicode: getter,
    unicodeSets: getter,

    // Annex B: Additional Properties of the RegExp.prototype Object
    compile: false  // UNSAFE and suppressed.
  },

  '%RegExpStringIteratorPrototype%': {
    // The %RegExpStringIteratorPrototype% Object
    '[[Proto]]': '%IteratorPrototype%',
    next: fn,
    '@@toStringTag': 'string',
  },

  // Indexed Collections

  Array: {
    // Properties of the Array Constructor
    '[[Proto]]': '%FunctionPrototype%',
    from: fn,
    isArray: fn,
    of: fn,
    prototype: '%ArrayPrototype%',
    '@@species': getter,

    // Failed tc39 proposal
    // https://tc39.es/proposal-relative-indexing-method/
    at: fn,
    // https://tc39.es/proposal-array-from-async/
    fromAsync: fn,
  },

  '%ArrayPrototype%': {
    // Properties of the Array Prototype Object
    length: 'number',
    concat: fn,
    constructor: 'Array',
    copyWithin: fn,
    entries: fn,
    every: fn,
    fill: fn,
    filter: fn,
    find: fn,
    findIndex: fn,
    flat: fn,
    flatMap: fn,
    forEach: fn,
    includes: fn,
    indexOf: fn,
    join: fn,
    keys: fn,
    lastIndexOf: fn,
    map: fn,
    pop: fn,
    push: fn,
    reduce: fn,
    reduceRight: fn,
    reverse: fn,
    shift: fn,
    slice: fn,
    some: fn,
    sort: fn,
    splice: fn,
    toLocaleString: fn,
    toString: fn,
    unshift: fn,
    values: fn,
    '@@iterator': fn,
    '@@unscopables': {
      '[[Proto]]': null,
      copyWithin: 'boolean',
      entries: 'boolean',
      fill: 'boolean',
      find: 'boolean',
      findIndex: 'boolean',
      flat: 'boolean',
      flatMap: 'boolean',
      includes: 'boolean',
      keys: 'boolean',
      values: 'boolean',
      // Failed tc39 proposal
      // https://tc39.es/proposal-relative-indexing-method/
      // Seen on FF Nightly 88.0a1
      at: 'boolean',
      // See https://github.com/tc39/proposal-array-find-from-last
      findLast: 'boolean',
      findLastIndex: 'boolean',
      // https://github.com/tc39/proposal-change-array-by-copy
      toReversed: 'boolean',
      toSorted: 'boolean',
      toSpliced: 'boolean',
      with: 'boolean',
      // https://github.com/tc39/proposal-array-grouping
      group: 'boolean',
      groupToMap: 'boolean',
      groupBy: 'boolean',
    },
    // See https://github.com/tc39/proposal-array-find-from-last
    findLast: fn,
    findLastIndex: fn,
    // https://github.com/tc39/proposal-change-array-by-copy
    toReversed: fn,
    toSorted: fn,
    toSpliced: fn,
    with: fn,
    // https://github.com/tc39/proposal-array-grouping
    group: fn, // Not in proposal? Where?
    groupToMap: fn, // Not in proposal? Where?
    groupBy: fn,
    // Failed tc39 proposal
    // https://tc39.es/proposal-relative-indexing-method/
    at: fn,
  },

  '%ArrayIteratorPrototype%': {
    // The %ArrayIteratorPrototype% Object
    '[[Proto]]': '%IteratorPrototype%',
    next: fn,
    '@@toStringTag': 'string',
  },

  // *** TypedArray Objects

  '%TypedArray%': {
    // Properties of the %TypedArray% Intrinsic Object
    '[[Proto]]': '%FunctionPrototype%',
    from: fn,
    of: fn,
    prototype: '%TypedArrayPrototype%',
    '@@species': getter,
  },

  '%TypedArrayPrototype%': {
    buffer: getter,
    byteLength: getter,
    byteOffset: getter,
    constructor: '%TypedArray%',
    copyWithin: fn,
    entries: fn,
    every: fn,
    fill: fn,
    filter: fn,
    find: fn,
    findIndex: fn,
    forEach: fn,
    includes: fn,
    indexOf: fn,
    join: fn,
    keys: fn,
    lastIndexOf: fn,
    length: getter,
    map: fn,
    reduce: fn,
    reduceRight: fn,
    reverse: fn,
    set: fn,
    slice: fn,
    some: fn,
    sort: fn,
    subarray: fn,
    toLocaleString: fn,
    toString: fn,
    values: fn,
    '@@iterator': fn,
    '@@toStringTag': getter,
    // Failed tc39 proposal
    // https://tc39.es/proposal-relative-indexing-method/
    at: fn,
    // See https://github.com/tc39/proposal-array-find-from-last
    findLast: fn,
    findLastIndex: fn,
    // https://github.com/tc39/proposal-change-array-by-copy
    toReversed: fn,
    toSorted: fn,
    with: fn,
  },

  // The TypedArray Constructors

  BigInt64Array: TypedArray('%BigInt64ArrayPrototype%'),
  BigUint64Array: TypedArray('%BigUint64ArrayPrototype%'),
  // https://github.com/tc39/proposal-float16array
  Float16Array: TypedArray('%Float16ArrayPrototype%'),
  Float32Array: TypedArray('%Float32ArrayPrototype%'),
  Float64Array: TypedArray('%Float64ArrayPrototype%'),
  Int16Array: TypedArray('%Int16ArrayPrototype%'),
  Int32Array: TypedArray('%Int32ArrayPrototype%'),
  Int8Array: TypedArray('%Int8ArrayPrototype%'),
  Uint16Array: TypedArray('%Uint16ArrayPrototype%'),
  Uint32Array: TypedArray('%Uint32ArrayPrototype%'),
  Uint8ClampedArray: TypedArray('%Uint8ClampedArrayPrototype%'),
  Uint8Array: {
    ...TypedArray('%Uint8ArrayPrototype%'),
    // https://github.com/tc39/proposal-arraybuffer-base64
    fromBase64: fn,
    // https://github.com/tc39/proposal-arraybuffer-base64
    fromHex: fn,
  },

  '%BigInt64ArrayPrototype%': TypedArrayPrototype('BigInt64Array'),
  '%BigUint64ArrayPrototype%': TypedArrayPrototype('BigUint64Array'),
  // https://github.com/tc39/proposal-float16array
  '%Float16ArrayPrototype%': TypedArrayPrototype('Float16Array'),
  '%Float32ArrayPrototype%': TypedArrayPrototype('Float32Array'),
  '%Float64ArrayPrototype%': TypedArrayPrototype('Float64Array'),
  '%Int16ArrayPrototype%': TypedArrayPrototype('Int16Array'),
  '%Int32ArrayPrototype%': TypedArrayPrototype('Int32Array'),
  '%Int8ArrayPrototype%': TypedArrayPrototype('Int8Array'),
  '%Uint16ArrayPrototype%': TypedArrayPrototype('Uint16Array'),
  '%Uint32ArrayPrototype%': TypedArrayPrototype('Uint32Array'),
  '%Uint8ClampedArrayPrototype%': TypedArrayPrototype('Uint8ClampedArray'),
  '%Uint8ArrayPrototype%': {
    ...TypedArrayPrototype('Uint8Array'),
    // https://github.com/tc39/proposal-arraybuffer-base64
    setFromBase64: fn,
    // https://github.com/tc39/proposal-arraybuffer-base64
    setFromHex: fn,
    // https://github.com/tc39/proposal-arraybuffer-base64
    toBase64: fn,
    // https://github.com/tc39/proposal-arraybuffer-base64
    toHex: fn,
  },

  // *** Keyed Collections

  Map: {
    // Properties of the Map Constructor
    '[[Proto]]': '%FunctionPrototype%',
    '@@species': getter,
    prototype: '%MapPrototype%',
    // https://github.com/tc39/proposal-array-grouping
    groupBy: fn,
  },

  '%MapPrototype%': {
    clear: fn,
    constructor: 'Map',
    delete: fn,
    entries: fn,
    forEach: fn,
    get: fn,
    has: fn,
    keys: fn,
    set: fn,
    size: getter,
    values: fn,
    '@@iterator': fn,
    '@@toStringTag': 'string',
  },

  '%MapIteratorPrototype%': {
    // The %MapIteratorPrototype% Object
    '[[Proto]]': '%IteratorPrototype%',
    next: fn,
    '@@toStringTag': 'string',
  },

  Set: {
    // Properties of the Set Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%SetPrototype%',
    '@@species': getter,
    // Seen on QuickJS
    groupBy: false,
  },

  '%SetPrototype%': {
    add: fn,
    clear: fn,
    constructor: 'Set',
    delete: fn,
    entries: fn,
    forEach: fn,
    has: fn,
    keys: fn,
    size: getter,
    values: fn,
    '@@iterator': fn,
    '@@toStringTag': 'string',
    // See https://github.com/tc39/proposal-set-methods
    intersection: fn,
    // See https://github.com/tc39/proposal-set-methods
    union: fn,
    // See https://github.com/tc39/proposal-set-methods
    difference: fn,
    // See https://github.com/tc39/proposal-set-methods
    symmetricDifference: fn,
    // See https://github.com/tc39/proposal-set-methods
    isSubsetOf: fn,
    // See https://github.com/tc39/proposal-set-methods
    isSupersetOf: fn,
    // See https://github.com/tc39/proposal-set-methods
    isDisjointFrom: fn,
  },

  '%SetIteratorPrototype%': {
    // The %SetIteratorPrototype% Object
    '[[Proto]]': '%IteratorPrototype%',
    next: fn,
    '@@toStringTag': 'string',
  },

  WeakMap: {
    // Properties of the WeakMap Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%WeakMapPrototype%',
  },

  '%WeakMapPrototype%': {
    constructor: 'WeakMap',
    delete: fn,
    get: fn,
    has: fn,
    set: fn,
    '@@toStringTag': 'string',
  },

  WeakSet: {
    // Properties of the WeakSet Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%WeakSetPrototype%',
  },

  '%WeakSetPrototype%': {
    add: fn,
    constructor: 'WeakSet',
    delete: fn,
    has: fn,
    '@@toStringTag': 'string',
  },

  // *** Structured Data

  ArrayBuffer: {
    // Properties of the ArrayBuffer Constructor
    '[[Proto]]': '%FunctionPrototype%',
    isView: fn,
    prototype: '%ArrayBufferPrototype%',
    '@@species': getter,
    // See https://github.com/Moddable-OpenSource/moddable/issues/523
    fromString: false,
    // See https://github.com/Moddable-OpenSource/moddable/issues/523
    fromBigInt: false,
  },

  '%ArrayBufferPrototype%': {
    byteLength: getter,
    constructor: 'ArrayBuffer',
    slice: fn,
    '@@toStringTag': 'string',
    // See https://github.com/Moddable-OpenSource/moddable/issues/523
    concat: false,
    // See https://github.com/tc39/proposal-resizablearraybuffer
    transfer: fn,
    resize: fn,
    resizable: getter,
    maxByteLength: getter,
    // https://github.com/tc39/proposal-arraybuffer-transfer
    transferToFixedLength: fn,
    detached: getter,
    // https://github.com/endojs/endo/pull/2309#issuecomment-2155513240
    // to be proposed
    transferToImmutable: fn,
    sliceToImmutable: fn,
    immutable: getter,
  },

  // If this exists, it is purely an artifact of how we currently shim
  // `transferToImmutable`. As natively implemented, there would be no
  // such extra prototype.
  '%ImmutableArrayBufferPrototype%': {
    '[[Proto]]': '%ArrayBufferPrototype%',
    byteLength: getter,
    slice: fn,
    // See https://github.com/endojs/endo/tree/master/packages/immutable-arraybuffer#purposeful-violation
    '@@toStringTag': 'string',
    // See https://github.com/tc39/proposal-resizablearraybuffer
    transfer: fn,
    resize: fn,
    resizable: getter,
    maxByteLength: getter,
    // https://github.com/tc39/proposal-arraybuffer-transfer
    transferToFixedLength: fn,
    detached: getter,
    // https://github.com/endojs/endo/pull/2309#issuecomment-2155513240
    // to be proposed
    transferToImmutable: fn,
    sliceToImmutable: fn,
    immutable: getter,
  },

  // SharedArrayBuffer Objects
  SharedArrayBuffer: false, // UNSAFE and purposely suppressed.
  '%SharedArrayBufferPrototype%': false, // UNSAFE and purposely suppressed.

  DataView: {
    // Properties of the DataView Constructor
    '[[Proto]]': '%FunctionPrototype%',
    BYTES_PER_ELEMENT: 'number', // Non std but undeletable on Safari.
    prototype: '%DataViewPrototype%',
  },

  '%DataViewPrototype%': {
    buffer: getter,
    byteLength: getter,
    byteOffset: getter,
    constructor: 'DataView',
    getBigInt64: fn,
    getBigUint64: fn,
    // https://github.com/tc39/proposal-float16array
    getFloat16: fn,
    getFloat32: fn,
    getFloat64: fn,
    getInt8: fn,
    getInt16: fn,
    getInt32: fn,
    getUint8: fn,
    getUint16: fn,
    getUint32: fn,
    setBigInt64: fn,
    setBigUint64: fn,
    // https://github.com/tc39/proposal-float16array
    setFloat16: fn,
    setFloat32: fn,
    setFloat64: fn,
    setInt8: fn,
    setInt16: fn,
    setInt32: fn,
    setUint8: fn,
    setUint16: fn,
    setUint32: fn,
    '@@toStringTag': 'string',
  },

  // Atomics
  Atomics: false, // UNSAFE and suppressed.

  JSON: {
    parse: fn,
    stringify: fn,
    '@@toStringTag': 'string',
    // https://github.com/tc39/proposal-json-parse-with-source/
    rawJSON: fn,
    isRawJSON: fn,
  },

  // *** Control Abstraction Objects

  // https://github.com/tc39/proposal-iterator-helpers
  Iterator: {
    // Properties of the Iterator Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%IteratorPrototype%',
    from: fn,
    // https://github.com/tc39/proposal-joint-iteration
    zip: fn,
    zipKeyed: fn,
    // https://github.com/tc39/proposal-iterator-sequencing
    concat: fn,
  },

  '%IteratorPrototype%': {
    // The %IteratorPrototype% Object
    '@@iterator': fn,
    // https://github.com/tc39/proposal-iterator-helpers
    constructor: 'Iterator',
    map: fn,
    filter: fn,
    take: fn,
    drop: fn,
    flatMap: fn,
    reduce: fn,
    toArray: fn,
    forEach: fn,
    some: fn,
    every: fn,
    find: fn,
    '@@toStringTag': 'string',
    // https://github.com/tc39/proposal-async-iterator-helpers
    toAsync: fn,
    // https://github.com/tc39/proposal-explicit-resource-management
    // See https://github.com/Moddable-OpenSource/moddable/issues/523#issuecomment-1942904505
    '@@dispose': false,
  },

  // https://github.com/tc39/proposal-iterator-helpers
  '%WrapForValidIteratorPrototype%': {
    '[[Proto]]': '%IteratorPrototype%',
    next: fn,
    return: fn,
  },

  // https://github.com/tc39/proposal-iterator-helpers
  '%IteratorHelperPrototype%': {
    '[[Proto]]': '%IteratorPrototype%',
    next: fn,
    return: fn,
    '@@toStringTag': 'string',
  },

  // https://github.com/tc39/proposal-async-iterator-helpers
  AsyncIterator: {
    // Properties of the Iterator Constructor
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%AsyncIteratorPrototype%',
    from: fn,
  },

  '%AsyncIteratorPrototype%': {
    // The %AsyncIteratorPrototype% Object
    '@@asyncIterator': fn,
    // https://github.com/tc39/proposal-async-iterator-helpers
    constructor: 'AsyncIterator',
    map: fn,
    filter: fn,
    take: fn,
    drop: fn,
    flatMap: fn,
    reduce: fn,
    toArray: fn,
    forEach: fn,
    some: fn,
    every: fn,
    find: fn,
    '@@toStringTag': 'string',
    // https://github.com/tc39/proposal-explicit-resource-management
    // See https://github.com/Moddable-OpenSource/moddable/issues/523#issuecomment-1942904505
    '@@asyncDispose': false,
  },

  // https://github.com/tc39/proposal-async-iterator-helpers
  '%WrapForValidAsyncIteratorPrototype%': {
    '[[Proto]]': '%AsyncIteratorPrototype%',
    next: fn,
    return: fn,
  },

  // https://github.com/tc39/proposal-async-iterator-helpers
  '%AsyncIteratorHelperPrototype%': {
    '[[Proto]]': '%AsyncIteratorPrototype%',
    next: fn,
    return: fn,
    '@@toStringTag': 'string',
  },

  '%InertGeneratorFunction%': {
    // Properties of the GeneratorFunction Constructor
    '[[Proto]]': '%InertFunction%',
    prototype: '%Generator%',
  },

  '%Generator%': {
    // Properties of the GeneratorFunction Prototype Object
    '[[Proto]]': '%FunctionPrototype%',
    constructor: '%InertGeneratorFunction%',
    prototype: '%GeneratorPrototype%',
    '@@toStringTag': 'string',
  },

  '%InertAsyncGeneratorFunction%': {
    // Properties of the AsyncGeneratorFunction Constructor
    '[[Proto]]': '%InertFunction%',
    prototype: '%AsyncGenerator%',
  },

  '%AsyncGenerator%': {
    // Properties of the AsyncGeneratorFunction Prototype Object
    '[[Proto]]': '%FunctionPrototype%',
    constructor: '%InertAsyncGeneratorFunction%',
    prototype: '%AsyncGeneratorPrototype%',
    // length prop added here for React Native jsc-android
    // https://github.com/endojs/endo/issues/660
    // https://github.com/react-native-community/jsc-android-buildscripts/issues/181
    length: 'number',
    '@@toStringTag': 'string',
  },

  '%GeneratorPrototype%': {
    // Properties of the Generator Prototype Object
    '[[Proto]]': '%IteratorPrototype%',
    constructor: '%Generator%',
    next: fn,
    return: fn,
    throw: fn,
    '@@toStringTag': 'string',
  },

  '%AsyncGeneratorPrototype%': {
    // Properties of the AsyncGenerator Prototype Object
    '[[Proto]]': '%AsyncIteratorPrototype%',
    constructor: '%AsyncGenerator%',
    next: fn,
    return: fn,
    throw: fn,
    '@@toStringTag': 'string',
  },

  // TODO: To be replaced with Promise.delegate
  //
  // The HandledPromise global variable shimmed by `@agoric/eventual-send/shim`
  // implements an initial version of the eventual send specification at:
  // https://github.com/tc39/proposal-eventual-send
  //
  // We will likely change this to add a property to Promise called
  // Promise.delegate and put static methods on it, which will necessitate
  // another permits change to update to the current proposed standard.
  HandledPromise: {
    '[[Proto]]': 'Promise',
    applyFunction: fn,
    applyFunctionSendOnly: fn,
    applyMethod: fn,
    applyMethodSendOnly: fn,
    get: fn,
    getSendOnly: fn,
    prototype: '%PromisePrototype%',
    resolve: fn,
  },

  // https://github.com/tc39/proposal-source-phase-imports?tab=readme-ov-file#js-module-source

  ModuleSource: {
    '[[Proto]]': '%AbstractModuleSource%',
    prototype: '%ModuleSourcePrototype%',
  },

  '%ModuleSourcePrototype%': {
    '[[Proto]]': '%AbstractModuleSourcePrototype%',
    constructor: 'ModuleSource',
    '@@toStringTag': 'string',
    // https://github.com/tc39/proposal-compartments
    bindings: getter,
    needsImport: getter,
    needsImportMeta: getter,
    // @endo/module-source provides a legacy interface
    imports: getter,
    exports: getter,
    reexports: getter,
  },

  '%AbstractModuleSource%': {
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%AbstractModuleSourcePrototype%',
  },

  '%AbstractModuleSourcePrototype%': {
    constructor: '%AbstractModuleSource%',
  },

  Promise: {
    // Properties of the Promise Constructor
    '[[Proto]]': '%FunctionPrototype%',
    all: fn,
    allSettled: fn,
    // https://github.com/Agoric/SES-shim/issues/550
    any: fn,
    prototype: '%PromisePrototype%',
    race: fn,
    reject: fn,
    resolve: fn,
    // https://github.com/tc39/proposal-promise-with-resolvers
    withResolvers: fn,
    '@@species': getter,
    // https://github.com/tc39/proposal-promise-try
    try: fn,
  },

  '%PromisePrototype%': {
    // Properties of the Promise Prototype Object
    catch: fn,
    constructor: 'Promise',
    finally: fn,
    then: fn,
    '@@toStringTag': 'string',
    // Non-standard, used in node to prevent async_hooks from breaking
    'UniqueSymbol(async_id_symbol)': accessor,
    'UniqueSymbol(trigger_async_id_symbol)': accessor,
    'UniqueSymbol(destroyed)': accessor,
  },

  '%InertAsyncFunction%': {
    // Properties of the AsyncFunction Constructor
    '[[Proto]]': '%InertFunction%',
    prototype: '%AsyncFunctionPrototype%',
  },

  '%AsyncFunctionPrototype%': {
    // Properties of the AsyncFunction Prototype Object
    '[[Proto]]': '%FunctionPrototype%',
    constructor: '%InertAsyncFunction%',
    // length prop added here for React Native jsc-android
    // https://github.com/endojs/endo/issues/660
    // https://github.com/react-native-community/jsc-android-buildscripts/issues/181
    length: 'number',
    '@@toStringTag': 'string',
  },

  // Reflection

  Reflect: {
    // The Reflect Object
    // Not a function object.
    apply: fn,
    construct: fn,
    defineProperty: fn,
    deleteProperty: fn,
    get: fn,
    getOwnPropertyDescriptor: fn,
    getPrototypeOf: fn,
    has: fn,
    isExtensible: fn,
    ownKeys: fn,
    preventExtensions: fn,
    set: fn,
    setPrototypeOf: fn,
    '@@toStringTag': 'string',
  },

  Proxy: {
    // Properties of the Proxy Constructor
    '[[Proto]]': '%FunctionPrototype%',
    revocable: fn,
  },

  // Appendix B

  // Annex B: Additional Properties of the Global Object

  escape: fn,
  unescape: fn,

  // Proposed

  '%UniqueCompartment%': {
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%CompartmentPrototype%',
    toString: fn,
  },

  '%InertCompartment%': {
    '[[Proto]]': '%FunctionPrototype%',
    prototype: '%CompartmentPrototype%',
    toString: fn,
  },

  '%CompartmentPrototype%': {
    constructor: '%InertCompartment%',
    evaluate: fn,
    globalThis: getter,
    name: getter,
    import: asyncFn,
    load: asyncFn,
    importNow: fn,
    module: fn,
    '@@toStringTag': 'string',
  },

  lockdown: fn,
  harden: { ...fn, isFake: 'boolean' },

  '%InitialGetStackString%': fn,
};$h͏_once.permitted(permitted);
})()
,
// === 17. ses ./src/intrinsics.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let cauterizeProperty,TypeError,WeakSet,arrayFilter,create,defineProperty,entries,freeze,getOwnPropertyDescriptor,getOwnPropertyDescriptors,globalThis,is,isPrimitive,hasOwn,values,weaksetHas,constantProperties,sharedGlobalPropertyNames,universalPropertyNames,permitted;$h͏_imports([["./cauterize-property.js", [["cauterizeProperty",[$h͏_a => (cauterizeProperty = $h͏_a)]]]],["./commons.js", [["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["WeakSet",[$h͏_a => (WeakSet = $h͏_a)]],["arrayFilter",[$h͏_a => (arrayFilter = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["entries",[$h͏_a => (entries = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["is",[$h͏_a => (is = $h͏_a)]],["isPrimitive",[$h͏_a => (isPrimitive = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]],["values",[$h͏_a => (values = $h͏_a)]],["weaksetHas",[$h͏_a => (weaksetHas = $h͏_a)]]]],["./permits.js", [["constantProperties",[$h͏_a => (constantProperties = $h͏_a)]],["sharedGlobalPropertyNames",[$h͏_a => (sharedGlobalPropertyNames = $h͏_a)]],["universalPropertyNames",[$h͏_a => (universalPropertyNames = $h͏_a)]],["permitted",[$h͏_a => (permitted = $h͏_a)]]]]]);

























/**
 * @import {Reporter} from './reporting-types.js'
 */

const isFunction = obj => typeof obj === 'function';

// Like defineProperty, but throws if it would modify an existing property.
// We use this to ensure that two conflicting attempts to define the same
// property throws, causing SES initialization to fail. Otherwise, a
// conflict between, for example, two of SES's internal permits might
// get masked as one overwrites the other. Accordingly, the thrown error
// complains of a "Conflicting definition".
function initProperty(obj, name, desc) {
  if (hasOwn(obj, name)) {
    const preDesc = getOwnPropertyDescriptor(obj, name);
    if (
      !preDesc ||
      !is(preDesc.value, desc.value) ||
      preDesc.get !== desc.get ||
      preDesc.set !== desc.set ||
      preDesc.writable !== desc.writable ||
      preDesc.enumerable !== desc.enumerable ||
      preDesc.configurable !== desc.configurable
    ) {
      throw TypeError(`Conflicting definitions of ${name}`);
    }
  }
  defineProperty(obj, name, desc);
}

// Like defineProperties, but throws if it would modify an existing property.
// This ensures that the intrinsics added to the intrinsics collector object
// graph do not overlap.
function initProperties(obj, descs) {
  for (const [name, desc] of entries(descs)) {
    initProperty(obj, name, desc);
  }
}

// sampleGlobals creates an intrinsics object, suitable for
// interinsicsCollector.addIntrinsics, from the named properties of a global
// object.
function sampleGlobals(globalObject, newPropertyNames) {
  const newIntrinsics = { __proto__: null };
  for (const [globalName, intrinsicName] of entries(newPropertyNames)) {
    if (hasOwn(globalObject, globalName)) {
      newIntrinsics[intrinsicName] = globalObject[globalName];
    }
  }
  return newIntrinsics;
}

/**
 * @param {Reporter} reporter
 */
       const makeIntrinsicsCollector = reporter => {
  /** @type {Record<any, any>} */
  const intrinsics = create(null);
  let pseudoNatives;

  const addIntrinsics = newIntrinsics => {
    initProperties(intrinsics, getOwnPropertyDescriptors(newIntrinsics));
  };
  freeze(addIntrinsics);

  // For each intrinsic, if it has a `.prototype` property, use the
  // permits to find out the intrinsic name for that prototype and add it
  // to the intrinsics.
  const completePrototypes = () => {
    for (const [name, intrinsic] of entries(intrinsics)) {
      if (isPrimitive(intrinsic)) {
        // eslint-disable-next-line no-continue
        continue;
      }
      if (!hasOwn(intrinsic, 'prototype')) {
        // eslint-disable-next-line no-continue
        continue;
      }
      const permit = permitted[name];
      if (typeof permit !== 'object') {
        throw TypeError(`Expected permit object at permits.${name}`);
      }
      const namePrototype = permit.prototype;
      if (!namePrototype) {
        cauterizeProperty(
          intrinsic,
          'prototype',
          false,
          `${name}.prototype`,
          reporter,
        );
        // eslint-disable-next-line no-continue
        continue;
      }
      if (
        typeof namePrototype !== 'string' ||
        !hasOwn(permitted, namePrototype)
      ) {
        throw TypeError(`Unrecognized ${name}.prototype permits entry`);
      }
      const intrinsicPrototype = intrinsic.prototype;
      if (hasOwn(intrinsics, namePrototype)) {
        if (intrinsics[namePrototype] !== intrinsicPrototype) {
          throw TypeError(`Conflicting bindings of ${namePrototype}`);
        }
        // eslint-disable-next-line no-continue
        continue;
      }
      intrinsics[namePrototype] = intrinsicPrototype;
    }
  };
  freeze(completePrototypes);

  const finalIntrinsics = () => {
    freeze(intrinsics);
    pseudoNatives = new WeakSet(arrayFilter(values(intrinsics), isFunction));
    return intrinsics;
  };
  freeze(finalIntrinsics);

  const isPseudoNative = obj => {
    if (!pseudoNatives) {
      throw TypeError(
        'isPseudoNative can only be called after finalIntrinsics',
      );
    }
    return weaksetHas(pseudoNatives, obj);
  };
  freeze(isPseudoNative);

  const intrinsicsCollector = {
    addIntrinsics,
    completePrototypes,
    finalIntrinsics,
    isPseudoNative,
  };
  freeze(intrinsicsCollector);

  addIntrinsics(constantProperties);
  addIntrinsics(sampleGlobals(globalThis, universalPropertyNames));

  return intrinsicsCollector;
};

/**
 * getGlobalIntrinsics()
 * Doesn't tame, delete, or modify anything. Samples globalObject to create an
 * intrinsics record containing only the permitted global variables, listed
 * by the intrinsic names appropriate for new globals, i.e., the globals of
 * newly constructed compartments.
 *
 * WARNING:
 * If run before lockdown, the returned intrinsics record will carry the
 * *original* unsafe (feral, untamed) bindings of these global variables.
 *
 * @param {object} globalObject
 * @param {Reporter} reporter
 */$h͏_once.makeIntrinsicsCollector(makeIntrinsicsCollector);
       const getGlobalIntrinsics = (globalObject, reporter) => {
  // TODO pass a proper reporter to `makeIntrinsicsCollector`
  const { addIntrinsics, finalIntrinsics } = makeIntrinsicsCollector(reporter);

  addIntrinsics(sampleGlobals(globalObject, sharedGlobalPropertyNames));

  return finalIntrinsics();
};$h͏_once.getGlobalIntrinsics(getGlobalIntrinsics);
})()
,
// === 18. ses ./src/permits-intrinsics.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let permitted,FunctionInstance,isAccessorPermit,Map,String,Symbol,TypeError,arrayFilter,arrayIncludes,arrayMap,entries,getOwnPropertyDescriptor,getPrototypeOf,isPrimitive,mapGet,hasOwn,ownKeys,symbolKeyFor,cauterizeProperty;$h͏_imports([["./permits.js", [["permitted",[$h͏_a => (permitted = $h͏_a)]],["FunctionInstance",[$h͏_a => (FunctionInstance = $h͏_a)]],["isAccessorPermit",[$h͏_a => (isAccessorPermit = $h͏_a)]]]],["./commons.js", [["Map",[$h͏_a => (Map = $h͏_a)]],["String",[$h͏_a => (String = $h͏_a)]],["Symbol",[$h͏_a => (Symbol = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["arrayFilter",[$h͏_a => (arrayFilter = $h͏_a)]],["arrayIncludes",[$h͏_a => (arrayIncludes = $h͏_a)]],["arrayMap",[$h͏_a => (arrayMap = $h͏_a)]],["entries",[$h͏_a => (entries = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["getPrototypeOf",[$h͏_a => (getPrototypeOf = $h͏_a)]],["isPrimitive",[$h͏_a => (isPrimitive = $h͏_a)]],["mapGet",[$h͏_a => (mapGet = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]],["ownKeys",[$h͏_a => (ownKeys = $h͏_a)]],["symbolKeyFor",[$h͏_a => (symbolKeyFor = $h͏_a)]]]],["./cauterize-property.js", [["cauterizeProperty",[$h͏_a => (cauterizeProperty = $h͏_a)]]]]]);
































































/**
 * @import {Reporter} from './reporting-types.js'
 */

/**
 * Removes all non-allowed properties found by recursively and
 * reflectively walking own property chains.
 *
 * @param {object} intrinsics
 * @param {(virtualizedNativeFunction: object) => void} markVirtualizedNativeFunction
 * @param {Reporter} reporter
 */
               function removeUnpermittedIntrinsics(
  intrinsics,
  markVirtualizedNativeFunction,
  reporter,
) {
  // These primitives are allowed for permits.
  const primitives = ['undefined', 'boolean', 'number', 'string', 'symbol'];

  // These symbols are allowed as well-known symbols
  const wellKnownSymbolNames = new Map(
    Symbol
      ? arrayMap(
          arrayFilter(
            entries(permitted['%SharedSymbol%']),
            ([name, permit]) =>
              permit === 'symbol' && typeof Symbol[name] === 'symbol',
          ),
          ([name]) => [Symbol[name], `@@${name}`],
        )
      : [],
  );

  /**
   * asStringPropertyName()
   *
   * @param {string} path
   * @param {string | symbol} prop
   */
  function asStringPropertyName(path, prop) {
    if (typeof prop === 'string') {
      return prop;
    }

    const wellKnownSymbol = mapGet(wellKnownSymbolNames, prop);

    if (typeof prop === 'symbol') {
      if (wellKnownSymbol) {
        return wellKnownSymbol;
      } else {
        const registeredKey = symbolKeyFor(prop);
        if (registeredKey !== undefined) {
          return `RegisteredSymbol(${registeredKey})`;
        } else {
          return `Unique${String(prop)}`;
        }
      }
    }

    throw TypeError(`Unexpected property name type ${path} ${prop}`);
  }

  /*
   * visitPrototype()
   * Validate the object's [[prototype]] against a permit.
   */
  function visitPrototype(path, obj, protoName) {
    if (isPrimitive(obj)) {
      throw TypeError(`Object expected: ${path}, ${String(obj)}, ${protoName}`);
    }
    const proto = getPrototypeOf(obj);

    // Null prototype.
    if (proto === null && protoName === null) {
      return;
    }

    // Assert: protoName, if provided, is a string.
    if (protoName !== undefined && typeof protoName !== 'string') {
      throw TypeError(`Malformed permit ${path}.__proto__`);
    }

    // If permit not specified, default to Object.prototype.
    if (proto === intrinsics[protoName || '%ObjectPrototype%']) {
      return;
    }

    // We can't clean [[Prototype]], therefore abort.
    throw TypeError(
      `Unexpected [[Prototype]] at ${path}.__proto__ (expected ${protoName || '%ObjectPrototype%'})`,
    );
  }

  /*
   * isAllowedPropertyValue()
   * enforce permit for a single property value.
   */
  function isAllowedPropertyValue(path, value, prop, permit) {
    if (typeof permit === 'object') {
      // eslint-disable-next-line no-use-before-define
      visitProperties(path, value, permit);
      // The property is allowed.
      return true;
    }

    if (permit === false) {
      // A boolan 'false' permit specifies the removal of a property.
      // We require a more specific permit instead of allowing 'true'.
      return false;
    }

    if (typeof permit === 'string') {
      // A string permit can have one of two meanings:

      if (prop === 'prototype' || prop === 'constructor') {
        // For prototype and constructor value properties, the permit
        // is the name of an intrinsic.
        // Assumption: prototype and constructor cannot be primitives.
        // Assert: the permit is the name of an intrinsic.
        // Assert: the property value is equal to that intrinsic.

        if (hasOwn(intrinsics, permit)) {
          if (value !== intrinsics[permit]) {
            throw TypeError(`Does not match permit for ${path}`);
          }
          return true;
        }
      } else {
        // For all other properties, the permit is the name of a primitive.
        // Assert: the permit is the name of a primitive.
        // Assert: the property value type is equal to that primitive.

        // eslint-disable-next-line no-lonely-if
        if (arrayIncludes(primitives, permit)) {
          // eslint-disable-next-line valid-typeof
          if (typeof value !== permit) {
            throw TypeError(
              `At ${path} expected ${permit} not ${typeof value}`,
            );
          }
          return true;
        }
      }
    }

    throw TypeError(
      `Unexpected property ${prop} with permit ${permit} at ${path}`,
    );
  }

  /*
   * isAllowedProperty()
   * Check whether a single property is allowed.
   */
  function isAllowedProperty(path, obj, prop, permit) {
    const desc = getOwnPropertyDescriptor(obj, prop);
    if (!desc) {
      throw TypeError(`Property ${prop} not found at ${path}`);
    }

    // Is this a value property?
    if (hasOwn(desc, 'value')) {
      if (isAccessorPermit(permit)) {
        throw TypeError(`Accessor expected at ${path}`);
      }
      return isAllowedPropertyValue(path, desc.value, prop, permit);
    }
    if (!isAccessorPermit(permit)) {
      throw TypeError(`Accessor not expected at ${path}`);
    }
    return (
      isAllowedPropertyValue(`${path}<get>`, desc.get, prop, permit.get) &&
      isAllowedPropertyValue(`${path}<set>`, desc.set, prop, permit.set)
    );
  }

  /*
   * getSubPermit()
   */
  function getSubPermit(obj, permit, prop) {
    const permitProp = prop === '__proto__' ? '--proto--' : prop;
    if (hasOwn(permit, permitProp)) {
      return permit[permitProp];
    }

    if (typeof obj === 'function') {
      if (hasOwn(FunctionInstance, permitProp)) {
        return FunctionInstance[permitProp];
      }
    }

    return undefined;
  }

  /*
   * visitProperties()
   * Visit all properties for a permit.
   */
  function visitProperties(path, obj, permit) {
    if (obj === undefined || obj === null) {
      return;
    }

    const protoName = permit['[[Proto]]'];
    visitPrototype(path, obj, protoName);

    if (typeof obj === 'function') {
      markVirtualizedNativeFunction(obj);
    }

    for (const prop of ownKeys(obj)) {
      const propString = asStringPropertyName(path, prop);
      const subPath = `${path}.${propString}`;
      const subPermit = getSubPermit(obj, permit, propString);

      if (!subPermit || !isAllowedProperty(subPath, obj, prop, subPermit)) {
        cauterizeProperty(obj, prop, subPermit === false, subPath, reporter);
      }
    }
  }

  // Start path with 'intrinsics' to clarify that properties are not
  // removed from the global object by the permitting operation.
  visitProperties('intrinsics', intrinsics, permitted);
}$h͏_once.default(      removeUnpermittedIntrinsics);
})()
,
// === 19. ses ./src/tame-function-constructors.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_FUNCTION,SyntaxError,TypeError,defineProperties,getPrototypeOf,setPrototypeOf,freeze,AsyncGeneratorFunctionInstance;$h͏_imports([["./commons.js", [["FERAL_FUNCTION",[$h͏_a => (FERAL_FUNCTION = $h͏_a)]],["SyntaxError",[$h͏_a => (SyntaxError = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["getPrototypeOf",[$h͏_a => (getPrototypeOf = $h͏_a)]],["setPrototypeOf",[$h͏_a => (setPrototypeOf = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["AsyncGeneratorFunctionInstance",[$h͏_a => (AsyncGeneratorFunctionInstance = $h͏_a)]]]]]);










// This module replaces the original `Function` constructor, and the original
// `%GeneratorFunction%`, `%AsyncFunction%` and `%AsyncGeneratorFunction%`,
// with safe replacements that throw if invoked.
//
// These are all reachable via syntax, so it isn't sufficient to just
// replace global properties with safe versions. Our main goal is to prevent
// access to the `Function` constructor through these starting points.
//
// After modules block is done, the originals must no longer be reachable,
// unless a copy has been made, and functions can only be created by syntax
// (using eval) or by invoking a previously saved reference to the originals.
//
// Typically, this module will not be used directly, but via the
// [lockdown - shim] which handles all necessary repairs and taming in SES.
//
// Relation to ECMA specifications
//
// The taming of constructors really wants to be part of the standard, because
// new constructors may be added in the future, reachable from syntax, and this
// list must be updated to match.
//
// In addition, the standard needs to define four new intrinsics for the safe
// replacement functions. See [./permits-intrinsics.js].
//
// Adapted from SES/Caja
// Copyright (C) 2011 Google Inc.
// https://github.com/google/caja/blob/master/src/com/google/caja/ses/startSES.js
// https://github.com/google/caja/blob/master/src/com/google/caja/ses/repairES5.js

/**
 * tameFunctionConstructors()
 * This block replaces the original Function constructor, and the original
 * %GeneratorFunction% %AsyncFunction% and %AsyncGeneratorFunction%, with
 * safe replacements that throw if invoked.
 */
               function tameFunctionConstructors() {
  try {
    // Verify that the method is not callable.
    // eslint-disable-next-line @endo/no-polymorphic-call
    FERAL_FUNCTION.prototype.constructor('return 1');
  } catch (ignore) {
    // Throws, no need to patch.
    return freeze({});
  }

  const newIntrinsics = {};

  /*
   * The process to repair constructors:
   * 1. Create an instance of the function by evaluating syntax
   * 2. Obtain the prototype from the instance
   * 3. Create a substitute tamed constructor
   * 4. Replace the original constructor with the tamed constructor
   * 5. Replace tamed constructor prototype property with the original one
   * 6. Replace its [[Prototype]] slot with the tamed constructor of Function
   */
  function repairFunction(name, intrinsicName, declaration) {
    let FunctionInstance;
    try {
      // eslint-disable-next-line no-eval, no-restricted-globals
      FunctionInstance = (0, eval)(declaration);
    } catch (e) {
      if (e instanceof SyntaxError) {
        // Prevent failure on platforms where async and/or generators
        // are not supported.
        return;
      }
      // Re-throw
      throw e;
    }
    const FunctionPrototype = getPrototypeOf(FunctionInstance);

    // Prevents the evaluation of source when calling constructor on the
    // prototype of functions.
    // eslint-disable-next-line func-names
    const InertConstructor = function () {
      throw TypeError(
        'Function.prototype.constructor is not a valid constructor.',
      );
    };
    defineProperties(InertConstructor, {
      prototype: { value: FunctionPrototype },
      name: {
        value: name,
        writable: false,
        enumerable: false,
        configurable: true,
      },
    });

    defineProperties(FunctionPrototype, {
      constructor: { value: InertConstructor },
    });

    // Reconstructs the inheritance among the new tamed constructors
    // to mirror the original specified in normal JS.
    if (InertConstructor !== FERAL_FUNCTION.prototype.constructor) {
      setPrototypeOf(InertConstructor, FERAL_FUNCTION.prototype.constructor);
    }

    newIntrinsics[intrinsicName] = InertConstructor;
  }

  // Here, the order of operation is important: Function needs to be repaired
  // first since the other repaired constructors need to inherit from the
  // tamed Function function constructor.

  repairFunction('Function', '%InertFunction%', '(function(){})');
  repairFunction(
    'GeneratorFunction',
    '%InertGeneratorFunction%',
    '(function*(){})',
  );
  repairFunction(
    'AsyncFunction',
    '%InertAsyncFunction%',
    '(async function(){})',
  );

  if (AsyncGeneratorFunctionInstance !== undefined) {
    repairFunction(
      'AsyncGeneratorFunction',
      '%InertAsyncGeneratorFunction%',
      '(async function*(){})',
    );
  }

  return newIntrinsics;
}$h͏_once.default(      tameFunctionConstructors);
})()
,
// === 20. ses ./src/tame-date-constructor.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Date,TypeError,apply,construct,defineProperties;$h͏_imports([["./commons.js", [["Date",[$h͏_a => (Date = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["apply",[$h͏_a => (apply = $h͏_a)]],["construct",[$h͏_a => (construct = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]]]]]);









               function tameDateConstructor() {
  const OriginalDate = Date;
  const DatePrototype = OriginalDate.prototype;

  // Use concise methods to obtain named functions without constructors.
  const tamedMethods = {
    /**
     * `%SharedDate%.now()` throw a `TypeError` starting with "secure mode".
     * See https://github.com/endojs/endo/issues/910#issuecomment-1581855420
     */
    now() {
      throw TypeError('secure mode Calling %SharedDate%.now() throws');
    },
  };

  /**
   * Tame the Date constructor.
   * See https://github.com/endojs/endo/issues/910#issuecomment-1581855420
   *
   * Common behavior
   *   * `new Date(x)` coerces x into a number and then returns a Date
   *     for that number of millis since the epoch
   *   * `new Date(NaN)` returns a Date object which stringifies to
   *     'Invalid Date'
   *   * `new Date(undefined)` returns a Date object which stringifies to
   *     'Invalid Date'
   *
   * OriginalDate (normal standard) behavior preserved by
   * `%InitialDate%`.
   *   * `Date(anything)` gives a string with the current time
   *   * `new Date()` returns the current time, as a Date object
   *
   * `%SharedDate%` behavior
   *   * `Date(anything)` throws a TypeError starting with "secure mode"
   *   * `new Date()` throws a TypeError starting with "secure mode"
   *
   * @param {{powers?: string}} [opts]
   */
  const makeDateConstructor = ({ powers = 'none' } = {}) => {
    let ResultDate;
    if (powers === 'original') {
      // eslint-disable-next-line no-shadow
      ResultDate = function Date(...rest) {
        if (new.target === undefined) {
          return apply(OriginalDate, undefined, rest);
        }
        return construct(OriginalDate, rest, new.target);
      };
    } else {
      // eslint-disable-next-line no-shadow
      ResultDate = function Date(...rest) {
        if (new.target === undefined) {
          throw TypeError(
            'secure mode Calling %SharedDate% constructor as a function throws',
          );
        }
        if (rest.length === 0) {
          throw TypeError(
            'secure mode Calling new %SharedDate%() with no arguments throws',
          );
        }
        return construct(OriginalDate, rest, new.target);
      };
    }

    defineProperties(ResultDate, {
      length: { value: 7 },
      prototype: {
        value: DatePrototype,
        writable: false,
        enumerable: false,
        configurable: false,
      },
      parse: {
        value: OriginalDate.parse,
        writable: true,
        enumerable: false,
        configurable: true,
      },
      UTC: {
        value: OriginalDate.UTC,
        writable: true,
        enumerable: false,
        configurable: true,
      },
    });
    return ResultDate;
  };
  const InitialDate = makeDateConstructor({ powers: 'original' });
  const SharedDate = makeDateConstructor({ powers: 'none' });

  defineProperties(InitialDate, {
    now: {
      value: OriginalDate.now,
      writable: true,
      enumerable: false,
      configurable: true,
    },
  });
  defineProperties(SharedDate, {
    now: {
      value: tamedMethods.now,
      writable: true,
      enumerable: false,
      configurable: true,
    },
  });

  defineProperties(DatePrototype, {
    constructor: { value: SharedDate },
  });

  return {
    '%InitialDate%': InitialDate,
    '%SharedDate%': SharedDate,
  };
}$h͏_once.default(      tameDateConstructor);
})()
,
// === 21. ses ./src/tame-math-object.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Math,TypeError,create,getOwnPropertyDescriptors,objectPrototype;$h͏_imports([["./commons.js", [["Math",[$h͏_a => (Math = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]],["objectPrototype",[$h͏_a => (objectPrototype = $h͏_a)]]]]]);







               function tameMathObject() {
  const originalMath = Math;
  const initialMath = originalMath; // to follow the naming pattern

  const { random: _, ...otherDescriptors } =
    getOwnPropertyDescriptors(originalMath);

  // Use concise methods to obtain named functions without constructors.
  const tamedMethods = {
    /**
     * `%SharedMath%.random()` throws a TypeError starting with "secure mode".
     * See https://github.com/endojs/endo/issues/910#issuecomment-1581855420
     */
    random() {
      throw TypeError('secure mode %SharedMath%.random() throws');
    },
  };

  const sharedMath = create(objectPrototype, {
    ...otherDescriptors,
    random: {
      value: tamedMethods.random,
      writable: true,
      enumerable: false,
      configurable: true,
    },
  });

  return {
    '%InitialMath%': initialMath,
    '%SharedMath%': sharedMath,
  };
}$h͏_once.default(      tameMathObject);
})()
,
// === 22. ses ./src/tame-regexp-constructor.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_REG_EXP,TypeError,construct,defineProperties,getOwnPropertyDescriptor,speciesSymbol;$h͏_imports([["./commons.js", [["FERAL_REG_EXP",[$h͏_a => (FERAL_REG_EXP = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["construct",[$h͏_a => (construct = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["speciesSymbol",[$h͏_a => (speciesSymbol = $h͏_a)]]]]]);








               function tameRegExpConstructor(regExpTaming = 'safe') {
  const RegExpPrototype = FERAL_REG_EXP.prototype;

  const makeRegExpConstructor = (_ = {}) => {
    // RegExp has non-writable static properties we need to omit.
    /**
     * @param  {Parameters<typeof FERAL_REG_EXP>} rest
     */
    const ResultRegExp = function RegExp(...rest) {
      if (new.target === undefined) {
        return FERAL_REG_EXP(...rest);
      }
      return construct(FERAL_REG_EXP, rest, new.target);
    };

    defineProperties(ResultRegExp, {
      length: { value: 2 },
      prototype: {
        value: RegExpPrototype,
        writable: false,
        enumerable: false,
        configurable: false,
      },
    });
    // Hermes does not have `Symbol.species`. We should support such platforms.
    if (speciesSymbol) {
      const speciesDesc = getOwnPropertyDescriptor(
        FERAL_REG_EXP,
        speciesSymbol,
      );
      if (!speciesDesc) {
        throw TypeError('no RegExp[Symbol.species] descriptor');
      }
      defineProperties(ResultRegExp, {
        [speciesSymbol]: speciesDesc,
      });
    }
    return ResultRegExp;
  };

  const InitialRegExp = makeRegExpConstructor();
  const SharedRegExp = makeRegExpConstructor();

  if (regExpTaming !== 'unsafe') {
    // @ts-expect-error Deleted properties must be optional
    delete RegExpPrototype.compile;
  }
  defineProperties(RegExpPrototype, {
    constructor: { value: SharedRegExp },
  });

  return {
    '%InitialRegExp%': InitialRegExp,
    '%SharedRegExp%': SharedRegExp,
  };
}$h͏_once.default(      tameRegExpConstructor);
})()
,
// === 23. ses ./src/enablements.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let toStringTagSymbol,iteratorSymbol;$h͏_imports([["./commons.js", [["toStringTagSymbol",[$h͏_a => (toStringTagSymbol = $h͏_a)]],["iteratorSymbol",[$h͏_a => (iteratorSymbol = $h͏_a)]]]]]);

/**
 * Exports {@code enablements}, a recursively defined
 * JSON record defining the optimum set of intrinsics properties
 * that need to be "repaired" before hardening is applied on
 * enviromments subject to the override mistake.
 *
 * @author JF Paradis
 * @author Mark S. Miller
 *
 * @module
 */

/**
 * <p>Because "repairing" replaces data properties with accessors, every
 * time a repaired property is accessed, the associated getter is invoked,
 * which degrades the runtime performance of all code executing in the
 * repaired enviromment, compared to the non-repaired case. In order
 * to maintain performance, we only repair the properties of objects
 * for which hardening causes a breakage of their normal intended usage.
 *
 * There are three unwanted cases:
 * <ul>
 * <li>Overriding properties on objects typically used as records,
 *     namely {@code "Object"} and {@code "Array"}. In the case of arrays,
 *     the situation is unintentional, a given program might not be aware
 *     that non-numerical properties are stored on the underlying object
 *     instance, not on the array. When an object is typically used as a
 *     map, we repair all of its prototype properties.
 * <li>Overriding properties on objects that provide defaults on their
 *     prototype and that programs typically set using an assignment, such as
 *     {@code "Error.prototype.message"} and {@code "Function.prototype.name"}
 *     (both default to "").
 * <li>Setting-up a prototype chain, where a constructor is set to extend
 *     another one. This is typically set by assignment, for example
 *     {@code "Child.prototype.constructor = Child"}, instead of invoking
 *     Object.defineProperty();
 *
 * <p>Each JSON record enumerates the disposition of the properties on
 * some corresponding intrinsic object.
 *
 * <p>For each such record, the values associated with its property
 * names can be:
 * <ul>
 * <li>true, in which case this property is simply repaired. The
 *     value associated with that property is not traversed. For
 *     example, {@code "Function.prototype.name"} leads to true,
 *     meaning that the {@code "name"} property of {@code
 *     "Function.prototype"} should be repaired (which is needed
 *     when inheriting from @code{Function} and setting the subclass's
 *     {@code "prototype.name"} property). If the property is
 *     already an accessor property, it is not repaired (because
 *     accessors are not subject to the override mistake).
 * <li>"*", in which case this property is not repaired but the
 *     value associated with that property are traversed and repaired.
 * <li>Another record, in which case this property is not repaired
 *     and that next record represents the disposition of the object
 *     which is its value. For example,{@code "FunctionPrototype"}
 *     leads to another record explaining which properties {@code
 *     Function.prototype} need to be repaired.
 */

/**
 * Minimal enablements when all the code is modern and known not to
 * step into the override mistake, except for the following pervasive
 * cases.
 */
       const minEnablements = {
  '%ObjectPrototype%': {
    toString: true,
  },

  '%FunctionPrototype%': {
    toString: true  // set by "rollup"
  },

  '%ErrorPrototype%': {
    name: true  // set by "precond", "ava", "node-fetch"
  },

  '%IteratorPrototype%': {
    toString: true,
    // https://github.com/tc39/proposal-iterator-helpers
    constructor: true,
    // https://github.com/tc39/proposal-iterator-helpers
    [toStringTagSymbol]: true,
  },
};

/**
 * Moderate enablements are usually good enough for legacy compat.
 */$h͏_once.minEnablements(minEnablements);
       const moderateEnablements = {
  ...minEnablements,

  '%ObjectPrototype%': {
    toString: true,
    valueOf: true,
  },

  '%ArrayPrototype%': {
    toString: true,
    push: true, // set by "Google Analytics"
    concat: true, // set by mobx generated code (old TS compiler?)
    [iteratorSymbol]: true  // set by mobx generated code (old TS compiler?)
  },

  '%IteratorPrototype%': {
    [iteratorSymbol]: true  // is sometimes used in custom iterators and generators implementations eg. @rive-app/canvas
  },

  // Function.prototype has no 'prototype' property to enable.
  // Function instances have their own 'name' and 'length' properties
  // which are configurable and non-writable. Thus, they are already
  // non-assignable anyway.
  '%FunctionPrototype%': {
    constructor: true, // set by "regenerator-runtime"
    bind: true, // set by "underscore", "express"
    toString: true  // set by "rollup"
  },

  '%ErrorPrototype%': {
    constructor: true, // set by "fast-json-patch", "node-fetch"
    message: true,
    name: true, // set by "precond", "ava", "node-fetch", "node 14"
    toString: true  // set by "bluebird"
  },

  '%TypeErrorPrototype%': {
    constructor: true, // set by "readable-stream"
    message: true, // set by "tape"
    name: true  // set by "readable-stream", "node 14"
  },

  '%SyntaxErrorPrototype%': {
    message: true, // to match TypeErrorPrototype.message
    name: true  // set by "node 14"
  },

  '%RangeErrorPrototype%': {
    message: true, // to match TypeErrorPrototype.message
    name: true  // set by "node 14"
  },

  '%URIErrorPrototype%': {
    message: true, // to match TypeErrorPrototype.message
    name: true  // set by "node 14"
  },

  '%EvalErrorPrototype%': {
    message: true, // to match TypeErrorPrototype.message
    name: true  // set by "node 14"
  },

  '%ReferenceErrorPrototype%': {
    message: true, // to match TypeErrorPrototype.message
    name: true  // set by "node 14"
  },

  // https://github.com/endojs/endo/issues/550
  '%AggregateErrorPrototype%': {
    message: true, // to match TypeErrorPrototype.message
    name: true  // set by "node 14"?
  },

  '%PromisePrototype%': {
    constructor: true  // set by "core-js"
  },

  '%TypedArrayPrototype%': '*', // set by https://github.com/feross/buffer

  '%Generator%': {
    constructor: true,
    name: true,
    toString: true,
  },
};

/**
 * The 'severe' enablement are needed because of issues tracked at
 * https://github.com/endojs/endo/issues/576
 *
 * They are like the `moderate` enablements except for the entries below.
 */$h͏_once.moderateEnablements(moderateEnablements);
       const severeEnablements = {
  ...moderateEnablements,

  /**
   * Rollup (as used at least by vega) and webpack
   * (as used at least by regenerator) both turn exports into assignments
   * to a big `exports` object that inherits directly from
   * `Object.prototype`. Some of the exported names we've seen include
   * `hasOwnProperty`, `constructor`, and `toString`. But the strategy used
   * by rollup and webpack potentionally turns any exported name
   * into an assignment rejected by the override mistake. That's why
   * the `severe` enablements takes the extreme step of enabling
   * everything on `Object.prototype`.
   *
   * In addition, code doing inheritance manually will often override
   * the `constructor` property on the new prototype by assignment. We've
   * seen this several times.
   *
   * The cost of enabling all these is that they create a miserable debugging
   * experience specifically on Node.
   * https://github.com/Agoric/agoric-sdk/issues/2324
   * explains how it confused the Node console.
   *
   * (TODO Reexamine the vscode situation. I think it may have improved
   * since the following paragraph was written.)
   *
   * The vscode debugger's object inspector shows the own data properties of
   * an object, which is typically what you want, but also shows both getter
   * and setter for every accessor property whether inherited or own.
   * With the `'*'` setting here, all the properties inherited from
   * `Object.prototype` are accessors, creating an unusable display as seen
   * at As explained at
   * https://github.com/endojs/endo/blob/master/packages/ses/docs/lockdown.md#overridetaming-options
   * Open the triangles at the bottom of that section.
   */
  '%ObjectPrototype%': '*',

  /**
   * The widely used Buffer defined at https://github.com/feross/buffer
   * on initialization, manually creates the equivalent of a subclass of
   * `TypedArray`, which it then initializes by assignment. These assignments
   * include enough of the `TypeArray` methods that here, the `severe`
   * enablements just enable them all.
   */
  '%TypedArrayPrototype%': '*',

  /**
   * Needed to work with Immer before https://github.com/immerjs/immer/pull/914
   * is accepted.
   */
  '%MapPrototype%': '*',

  /**
   * Needed to work with Immer before https://github.com/immerjs/immer/pull/914
   * is accepted.
   */
  '%SetPrototype%': '*',
};$h͏_once.severeEnablements(severeEnablements);
})()
,
// === 24. ses ./src/enable-property-overrides.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Set,String,TypeError,arrayForEach,defineProperty,getOwnPropertyDescriptor,getOwnPropertyDescriptors,isPrimitive,hasOwn,ownKeys,setHas,minEnablements,moderateEnablements,severeEnablements;$h͏_imports([["./commons.js", [["Set",[$h͏_a => (Set = $h͏_a)]],["String",[$h͏_a => (String = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["arrayForEach",[$h͏_a => (arrayForEach = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]],["isPrimitive",[$h͏_a => (isPrimitive = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]],["ownKeys",[$h͏_a => (ownKeys = $h͏_a)]],["setHas",[$h͏_a => (setHas = $h͏_a)]]]],["./enablements.js", [["minEnablements",[$h͏_a => (minEnablements = $h͏_a)]],["moderateEnablements",[$h͏_a => (moderateEnablements = $h͏_a)]],["severeEnablements",[$h͏_a => (severeEnablements = $h͏_a)]]]]]);
























/** @import {Reporter} from './reporting-types.js' */

/**
 * For a special set of properties defined in the `enablement` list,
 * `enablePropertyOverrides` ensures that the effect of freezing does not
 * suppress the ability to override these properties on derived objects by
 * simple assignment.
 *
 * Because of lack of sufficient foresight at the time, ES5 unfortunately
 * specified that a simple assignment to a non-existent property must fail if
 * it would override an non-writable data property of the same name in the
 * shadow of the prototype chain. In retrospect, this was a mistake, the
 * so-called "override mistake". But it is now too late and we must live with
 * the consequences.
 *
 * As a result, simply freezing an object to make it tamper proof has the
 * unfortunate side effect of breaking previously correct code that is
 * considered to have followed JS best practices, if this previous code used
 * assignment to override.
 *
 * For the enabled properties, `enablePropertyOverrides` effectively shims what
 * the assignment behavior would have been in the absence of the override
 * mistake. However, the shim produces an imperfect emulation. It shims the
 * behavior by turning these data properties into accessor properties, where
 * the accessor's getter and setter provide the desired behavior. For
 * non-reflective operations, the illusion is perfect. However, reflective
 * operations like `getOwnPropertyDescriptor` see the descriptor of an accessor
 * property rather than the descriptor of a data property. At the time of this
 * writing, this is the best we know how to do.
 *
 * To the getter of the accessor we add a property named
 * `'originalValue'` whose value is, as it says, the value that the
 * data property had before being converted to an accessor property. We add
 * this extra property to the getter for two reason:
 *
 * The harden algorithm walks the own properties reflectively, i.e., with
 * `getOwnPropertyDescriptor` semantics, rather than `[[Get]]` semantics. When
 * it sees an accessor property, it does not invoke the getter. Rather, it
 * proceeds to walk both the getter and setter as part of its transitive
 * traversal. Without this extra property, `enablePropertyOverrides` would have
 * hidden the original data property value from `harden`, which would be bad.
 * Instead, by exposing that value in an own data property on the getter,
 * `harden` finds and walks it anyway.
 *
 * We enable a form of cooperative emulation, giving reflective code an
 * opportunity to cooperate in upholding the illusion. When such cooperative
 * reflective code sees an accessor property, where the accessor's getter
 * has an `originalValue` property, it knows that the getter is
 * alleging that it is the result of the `enablePropertyOverrides` conversion
 * pattern, so it can decide to cooperatively "pretend" that it sees a data
 * property with that value.
 *
 * @param {Record<string, any>} intrinsics
 * @param {'min' | 'moderate' | 'severe'} overrideTaming
 * @param {Reporter} reporter
 * @param {Iterable<string | symbol>} [overrideDebug]
 */
               function enablePropertyOverrides(
  intrinsics,
  overrideTaming,
  { warn },
  overrideDebug = [],
) {
  const debugProperties = new Set(overrideDebug);
  function enable(path, obj, prop, desc) {
    if ('value' in desc && desc.configurable) {
      const { value } = desc;

      const isDebug = setHas(debugProperties, prop);

      // We use concise method syntax to be `this` sensitive, but still
      // omit a prototype property or [[Construct]] behavior.
      // @ts-expect-error We know there is an accessor descriptor there
      const { get: getter, set: setter } = getOwnPropertyDescriptor(
        {
          get [prop]() {
            return value;
          },
          set [prop](newValue) {
            if (obj === this) {
              throw TypeError(
                `Cannot assign to read only property '${String(
                  prop,
                )}' of '${path}'`,
              );
            }
            if (hasOwn(this, prop)) {
              this[prop] = newValue;
            } else {
              if (isDebug) {
                warn(TypeError(`Override property ${prop}`));
              }
              defineProperty(this, prop, {
                value: newValue,
                writable: true,
                enumerable: true,
                configurable: true,
              });
            }
          },
        },
        prop,
      );

      defineProperty(getter, 'originalValue', {
        value,
        writable: false,
        enumerable: false,
        configurable: false,
      });

      defineProperty(obj, prop, {
        get: getter,
        set: setter,
        enumerable: desc.enumerable,
        configurable: desc.configurable,
      });
    }
  }

  function enableProperty(path, obj, prop) {
    const desc = getOwnPropertyDescriptor(obj, prop);
    if (!desc) {
      return;
    }
    enable(path, obj, prop, desc);
  }

  function enableAllProperties(path, obj) {
    const descs = getOwnPropertyDescriptors(obj);
    if (!descs) {
      return;
    }
    // TypeScript does not allow symbols to be used as indexes because it
    // cannot recokon types of symbolized properties.
    arrayForEach(ownKeys(descs), prop => enable(path, obj, prop, descs[prop]));
  }

  function enableProperties(path, obj, plan) {
    for (const prop of ownKeys(plan)) {
      const desc = getOwnPropertyDescriptor(obj, prop);
      if (!desc || desc.get || desc.set) {
        // No not a value property, nothing to do.
        // eslint-disable-next-line no-continue
        continue;
      }

      // In case `prop` is a symbol, we first coerce it with `String`,
      // purely for diagnostic purposes.
      const subPath = `${path}.${String(prop)}`;
      const subPlan = plan[prop];

      if (subPlan === true) {
        enableProperty(subPath, obj, prop);
      } else if (subPlan === '*') {
        enableAllProperties(subPath, desc.value);
      } else if (!isPrimitive(subPlan)) {
        enableProperties(subPath, desc.value, subPlan);
      } else {
        throw TypeError(`Unexpected override enablement plan ${subPath}`);
      }
    }
  }

  let plan;
  switch (overrideTaming) {
    case 'min': {
      plan = minEnablements;
      break;
    }
    case 'moderate': {
      plan = moderateEnablements;
      break;
    }
    case 'severe': {
      plan = severeEnablements;
      break;
    }
    default: {
      throw TypeError(`unrecognized overrideTaming ${overrideTaming}`);
    }
  }

  // Do the repair.
  enableProperties('root', intrinsics, plan);
}$h͏_once.default(      enablePropertyOverrides);
})()
,
// === 25. ses ./src/tame-locale-methods.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Number,String,TypeError,defineProperty,getOwnPropertyNames,isPrimitive,regexpExec,assert;$h͏_imports([["./commons.js", [["Number",[$h͏_a => (Number = $h͏_a)]],["String",[$h͏_a => (String = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["getOwnPropertyNames",[$h͏_a => (getOwnPropertyNames = $h͏_a)]],["isPrimitive",[$h͏_a => (isPrimitive = $h͏_a)]],["regexpExec",[$h͏_a => (regexpExec = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);










const { Fail, quote: q } = assert;

const localePattern = /^(\w*[a-z])Locale([A-Z]\w*)$/;

// Use concise methods to obtain named functions without constructor
// behavior or `.prototype` property.
const tamedMethods = {
  // See https://tc39.es/ecma262/#sec-string.prototype.localecompare
  localeCompare(arg) {
    if (this === null || this === undefined) {
      throw TypeError(
        'Cannot localeCompare with null or undefined "this" value',
      );
    }
    const s = `${this}`;
    const that = `${arg}`;
    if (s < that) {
      return -1;
    }
    if (s > that) {
      return 1;
    }
    s === that || Fail`expected ${q(s)} and ${q(that)} to compare`;
    return 0;
  },

  toString() {
    return `${this}`;
  },
};

const nonLocaleCompare = tamedMethods.localeCompare;
const numberToString = tamedMethods.toString;

               function tameLocaleMethods(intrinsics, localeTaming = 'safe') {
  if (localeTaming === 'unsafe') {
    return;
  }

  defineProperty(String.prototype, 'localeCompare', {
    value: nonLocaleCompare,
  });

  for (const intrinsicName of getOwnPropertyNames(intrinsics)) {
    const intrinsic = intrinsics[intrinsicName];
    if (!isPrimitive(intrinsic)) {
      for (const methodName of getOwnPropertyNames(intrinsic)) {
        const match = regexpExec(localePattern, methodName);
        if (match) {
          typeof intrinsic[methodName] === 'function' ||
            Fail`expected ${q(methodName)} to be a function`;
          const nonLocaleMethodName = `${match[1]}${match[2]}`;
          const method = intrinsic[nonLocaleMethodName];
          typeof method === 'function' ||
            Fail`function ${q(nonLocaleMethodName)} not found`;
          defineProperty(intrinsic, methodName, { value: method });
        }
      }
    }
  }

  // Numbers are special because toString accepts a radix instead of ignoring
  // all of the arguments that we would otherwise forward.
  defineProperty(Number.prototype, 'toLocaleString', {
    value: numberToString,
  });
}$h͏_once.default(      tameLocaleMethods);
})()
,
// === 26. ses ./src/make-eval-function.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([]);/**
 * makeEvalFunction()
 * A safe version of the native eval function which relies on
 * the safety of `safe-eval` for confinement, unless `no-eval`
 * is specified (then a TypeError is thrown on use).
 *
 * @param {Function} evaluator
 */
       const makeEvalFunction = evaluator => {
  // We use the concise method syntax to create an eval without a
  // [[Construct]] behavior (such that the invocation "new eval()" throws
  // TypeError: eval is not a constructor"), but which still accepts a
  // 'this' binding.
  const newEval = {
    eval(source) {
      if (typeof source !== 'string') {
        // As per the runtime semantic of PerformEval [ECMAScript 18.2.1.1]:
        // If Type(source) is not String, return source.
        // TODO Recent proposals from Mike Samuel may change this non-string
        // rule. Track.
        return source;
      }
      return evaluator(source);
    },
  }.eval;

  return newEval;
};$h͏_once.makeEvalFunction(makeEvalFunction);
})()
,
// === 27. ses ./src/make-function-constructor.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_FUNCTION,arrayJoin,arrayPop,defineProperties,getPrototypeOf,assert;$h͏_imports([["./commons.js", [["FERAL_FUNCTION",[$h͏_a => (FERAL_FUNCTION = $h͏_a)]],["arrayJoin",[$h͏_a => (arrayJoin = $h͏_a)]],["arrayPop",[$h͏_a => (arrayPop = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["getPrototypeOf",[$h͏_a => (getPrototypeOf = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);








const { Fail } = assert;

/*
 * makeFunctionConstructor()
 * A safe version of the native Function which relies on
 * the safety of `safe-eval` for confinement, unless `no-eval`
 * is specified (then a TypeError is thrown on use).
 */
       const makeFunctionConstructor = evaluator => {
  // Define an unused parameter to ensure Function.length === 1
  const newFunction = function Function(_body) {
    // Sanitize all parameters at the entry point.
    // eslint-disable-next-line prefer-rest-params
    const bodyText = `${arrayPop(arguments) || ''}`;
    // eslint-disable-next-line prefer-rest-params
    const parameters = `${arrayJoin(arguments, ',')}`;

    // Are parameters and bodyText valid code, or is someone
    // attempting an injection attack? This will throw a SyntaxError if:
    // - parameters doesn't parse as parameters
    // - bodyText doesn't parse as a function body
    // - either contain a call to super() or references a super property.
    //
    // It seems that XS may still be vulnerable to the attack explained at
    // https://github.com/tc39/ecma262/pull/2374#issuecomment-813769710
    // where `new Function('/*', '*/ ) {')` would incorrectly validate.
    // Before we worried about this, we check the parameters and bodyText
    // together in one call
    // ```js
    // new FERAL_FUNCTION(parameters, bodyTest);
    // ```
    // However, this check is vulnerable to that bug. Aside from that case,
    // all engines do seem to validate the parameters, taken by themselves,
    // correctly. And all engines do seem to validate the bodyText, taken
    // by itself correctly. So with the following two checks, SES builds a
    // correct safe `Function` constructor by composing two calls to an
    // original unsafe `Function` constructor that may suffer from this bug
    // but is otherwise correctly validating.
    //
    // eslint-disable-next-line no-new
    new FERAL_FUNCTION(parameters, '');
    // eslint-disable-next-line no-new
    new FERAL_FUNCTION(bodyText);

    // Safe to be combined. Defeat potential trailing comments.
    // TODO: since we create an anonymous function, the 'this' value
    // isn't bound to the global object as per specs, but set as undefined.
    const src = `(function anonymous(${parameters}\n) {\n${bodyText}\n})`;
    return evaluator(src);
  };

  defineProperties(newFunction, {
    // Ensure that any function created in any evaluator in a realm is an
    // instance of Function in any evaluator of the same realm.
    prototype: {
      value: FERAL_FUNCTION.prototype,
      writable: false,
      enumerable: false,
      configurable: false,
    },
  });

  // Assert identity of Function.__proto__ accross all compartments
  getPrototypeOf(FERAL_FUNCTION) === FERAL_FUNCTION.prototype ||
    Fail`Function prototype is the same accross compartments`;
  getPrototypeOf(newFunction) === FERAL_FUNCTION.prototype ||
    Fail`Function constructor prototype is the same across compartments`;

  return newFunction;
};$h͏_once.makeFunctionConstructor(makeFunctionConstructor);
})()
,
// === 28. ses ./src/global-object.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let TypeError,assign,create,defineProperty,entries,freeze,hasOwn,unscopablesSymbol,makeEvalFunction,makeFunctionConstructor,constantProperties,universalPropertyNames;$h͏_imports([["./commons.js", [["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["assign",[$h͏_a => (assign = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["entries",[$h͏_a => (entries = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]],["unscopablesSymbol",[$h͏_a => (unscopablesSymbol = $h͏_a)]]]],["./make-eval-function.js", [["makeEvalFunction",[$h͏_a => (makeEvalFunction = $h͏_a)]]]],["./make-function-constructor.js", [["makeFunctionConstructor",[$h͏_a => (makeFunctionConstructor = $h͏_a)]]]],["./permits.js", [["constantProperties",[$h͏_a => (constantProperties = $h͏_a)]],["universalPropertyNames",[$h͏_a => (universalPropertyNames = $h͏_a)]]]]]);













/**
 * The host's ordinary global object is not provided by a `with` block, so
 * assigning to Symbol.unscopables has no effect.
 * Since this shim uses `with` blocks to create a confined lexical scope for
 * guest programs, we cannot emulate the proper behavior.
 * With this shim, assigning Symbol.unscopables causes the given lexical
 * names to fall through to the terminal scope proxy.
 * But, we can install this setter to prevent a program from proceding on
 * this false assumption.
 *
 * @param {object} globalObject
 */
       const setGlobalObjectSymbolUnscopables = globalObject => {
  defineProperty(
    globalObject,
    unscopablesSymbol,
    freeze(
      assign(create(null), {
        set: freeze(() => {
          throw TypeError(
            `Cannot set Symbol.unscopables of a Compartment's globalThis`,
          );
        }),
        enumerable: false,
        configurable: false,
      }),
    ),
  );
};

/**
 * setGlobalObjectConstantProperties()
 * Initializes a new global object using a process similar to ECMA specifications
 * (SetDefaultGlobalBindings). This process is split between this function and
 * `setGlobalObjectMutableProperties`.
 *
 * @param {object} globalObject
 */$h͏_once.setGlobalObjectSymbolUnscopables(setGlobalObjectSymbolUnscopables);
       const setGlobalObjectConstantProperties = globalObject => {
  for (const [name, constant] of entries(constantProperties)) {
    defineProperty(globalObject, name, {
      value: constant,
      writable: false,
      enumerable: false,
      configurable: false,
    });
  }
};

/**
 * setGlobalObjectMutableProperties()
 * Create new global object using a process similar to ECMA specifications
 * (portions of SetRealmGlobalObject and SetDefaultGlobalBindings).
 * `newGlobalPropertyNames` should be either `initialGlobalPropertyNames` or
 * `sharedGlobalPropertyNames`.
 *
 * @param {object} globalObject
 * @param {object} args
 * @param {object} args.intrinsics
 * @param {object} args.newGlobalPropertyNames
 * @param {Function} args.makeCompartmentConstructor
 * @param {(object) => void} args.markVirtualizedNativeFunction
 * @param {Compartment} [args.parentCompartment]
 */$h͏_once.setGlobalObjectConstantProperties(setGlobalObjectConstantProperties);
       const setGlobalObjectMutableProperties = (
  globalObject,
  {
    intrinsics,
    newGlobalPropertyNames,
    makeCompartmentConstructor,
    markVirtualizedNativeFunction,
    parentCompartment,
  },
) => {
  for (const [name, intrinsicName] of entries(universalPropertyNames)) {
    if (hasOwn(intrinsics, intrinsicName)) {
      defineProperty(globalObject, name, {
        value: intrinsics[intrinsicName],
        writable: true,
        enumerable: false,
        configurable: true,
      });
    }
  }

  for (const [name, intrinsicName] of entries(newGlobalPropertyNames)) {
    if (hasOwn(intrinsics, intrinsicName)) {
      defineProperty(globalObject, name, {
        value: intrinsics[intrinsicName],
        writable: true,
        enumerable: false,
        configurable: true,
      });
    }
  }

  const perCompartmentGlobals = {
    globalThis: globalObject,
  };

  perCompartmentGlobals.Compartment = freeze(
    makeCompartmentConstructor(
      makeCompartmentConstructor,
      intrinsics,
      markVirtualizedNativeFunction,
      {
        parentCompartment,
        enforceNew: true,
      },
    ),
  );

  // TODO These should still be tamed according to the permits before
  // being made available.
  for (const [name, value] of entries(perCompartmentGlobals)) {
    defineProperty(globalObject, name, {
      value,
      writable: true,
      enumerable: false,
      configurable: true,
    });
    if (typeof value === 'function') {
      markVirtualizedNativeFunction(value);
    }
  }
};

/**
 * setGlobalObjectEvaluators()
 * Set the eval and the Function evaluator on the global object with given evalTaming policy.
 *
 * @param {object} globalObject
 * @param {Function} evaluator
 * @param {(object) => void} markVirtualizedNativeFunction
 */$h͏_once.setGlobalObjectMutableProperties(setGlobalObjectMutableProperties);
       const setGlobalObjectEvaluators = (
  globalObject,
  evaluator,
  markVirtualizedNativeFunction,
) => {
  {
    const f = freeze(makeEvalFunction(evaluator));
    markVirtualizedNativeFunction(f);
    defineProperty(globalObject, 'eval', {
      value: f,
      writable: true,
      enumerable: false,
      configurable: true,
    });
  }
  {
    const f = freeze(makeFunctionConstructor(evaluator));
    markVirtualizedNativeFunction(f);
    defineProperty(globalObject, 'Function', {
      value: f,
      writable: true,
      enumerable: false,
      configurable: true,
    });
  }
};$h͏_once.setGlobalObjectEvaluators(setGlobalObjectEvaluators);
})()
,
// === 29. ses ./src/strict-scope-terminator.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Proxy,String,TypeError,ReferenceError,create,freeze,getOwnPropertyDescriptors,assert;$h͏_imports([["./commons.js", [["Proxy",[$h͏_a => (Proxy = $h͏_a)]],["String",[$h͏_a => (String = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["ReferenceError",[$h͏_a => (ReferenceError = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);










const { Fail, quote: q } = assert;

/**
 * `freeze` but not `harden` the proxy target so it remains trapping.
 * Thus, it should not be shared outside this module.
 *
 * @see https://github.com/endojs/endo/blob/master/packages/ses/docs/preparing-for-stabilize.md
 */
const objTarget = freeze({ __proto__: null });

/**
 * alwaysThrowHandler
 * This is an object that throws if any property is called. It's used as
 * a proxy handler which throws on any trap called.
 * It's made from a proxy with a get trap that throws. It's safe to
 * create one and share it between all Proxy handlers.
 */
       const alwaysThrowHandler = new Proxy(
  objTarget,
  freeze({
    get(_shadow, prop) {
      Fail`Please report unexpected scope handler trap: ${q(String(prop))}`;
    },
  }),
);

/*
 * scopeProxyHandlerProperties
 * scopeTerminatorHandler manages a strictScopeTerminator Proxy which serves as
 * the final scope boundary that will always return "undefined" in order
 * to prevent access to "start compartment globals".
 */$h͏_once.alwaysThrowHandler(alwaysThrowHandler);
const scopeProxyHandlerProperties = {
  get(_shadow, _prop) {
    return undefined;
  },

  set(_shadow, prop, _value) {
    // We should only hit this if the has() hook returned true matches the v8
    // ReferenceError message "Uncaught ReferenceError: xyz is not defined"
    throw ReferenceError(`${String(prop)} is not defined`);
  },

  has(_shadow, prop) {
    // we must at least return true for all properties on the realm globalThis
    return true;
  },

  // note: this is likely a bug of safari
  // https://bugs.webkit.org/show_bug.cgi?id=195534
  getPrototypeOf(_shadow) {
    return null;
  },

  // See https://github.com/endojs/endo/issues/1510
  // TODO: report as bug to v8 or Chrome, and record issue link here.
  getOwnPropertyDescriptor(_shadow, prop) {
    // Coerce with `String` in case prop is a symbol.
    const quotedProp = q(String(prop));
    // eslint-disable-next-line @endo/no-polymorphic-call
    console.warn(
      `getOwnPropertyDescriptor trap on scopeTerminatorHandler for ${quotedProp}`,
      TypeError().stack,
    );
    return undefined;
  },

  // See https://github.com/endojs/endo/issues/1490
  // TODO Report bug to JSC or Safari
  ownKeys(_shadow) {
    return [];
  },
};

// The scope handler's prototype is a proxy that throws if any trap other
// than get/set/has are run (like getOwnPropertyDescriptors, apply,
// getPrototypeOf).
       const strictScopeTerminatorHandler = freeze(
  create(
    alwaysThrowHandler,
    getOwnPropertyDescriptors(scopeProxyHandlerProperties),
  ),
);$h͏_once.strictScopeTerminatorHandler(strictScopeTerminatorHandler);

       const strictScopeTerminator = new Proxy(
  objTarget,
  strictScopeTerminatorHandler,
);$h͏_once.strictScopeTerminator(strictScopeTerminator);
})()
,
// === 30. ses ./src/sloppy-globals-scope-terminator.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Proxy,create,freeze,getOwnPropertyDescriptors,reflectSet,strictScopeTerminatorHandler,alwaysThrowHandler;$h͏_imports([["./commons.js", [["Proxy",[$h͏_a => (Proxy = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]],["reflectSet",[$h͏_a => (reflectSet = $h͏_a)]]]],["./strict-scope-terminator.js", [["strictScopeTerminatorHandler",[$h͏_a => (strictScopeTerminatorHandler = $h͏_a)]],["alwaysThrowHandler",[$h͏_a => (alwaysThrowHandler = $h͏_a)]]]]]);











/**
 * `freeze` but not `harden` the proxy target so it remains trapping.
 * Thus, it should not be shared outside this module.
 *
 * @see https://github.com/endojs/endo/blob/master/packages/ses/docs/preparing-for-stabilize.md
 */
const objTarget = freeze({ __proto__: null });

/*
 * createSloppyGlobalsScopeTerminator()
 * strictScopeTerminatorHandler manages a scopeTerminator Proxy which serves as
 * the final scope boundary that will always return "undefined" in order
 * to prevent access to "start compartment globals". When "sloppyGlobalsMode"
 * is true, the Proxy will perform sets on the "globalObject".
 */
       const createSloppyGlobalsScopeTerminator = globalObject => {
  const scopeProxyHandlerProperties = {
    // inherit scopeTerminator behavior
    ...strictScopeTerminatorHandler,

    // Redirect set properties to the globalObject.
    set(_shadow, prop, value) {
      return reflectSet(globalObject, prop, value);
    },

    // Always claim to have a potential property in order to be the recipient of a set
    has(_shadow, _prop) {
      return true;
    },
  };

  // The scope handler's prototype is a proxy that throws if any trap other
  // than get/set/has are run (like getOwnPropertyDescriptors, apply,
  // getPrototypeOf).
  const sloppyGlobalsScopeTerminatorHandler = freeze(
    create(
      alwaysThrowHandler,
      getOwnPropertyDescriptors(scopeProxyHandlerProperties),
    ),
  );

  const sloppyGlobalsScopeTerminator = new Proxy(
    objTarget,
    sloppyGlobalsScopeTerminatorHandler,
  );

  return sloppyGlobalsScopeTerminator;
};$h͏_once.createSloppyGlobalsScopeTerminator(createSloppyGlobalsScopeTerminator);
freeze(createSloppyGlobalsScopeTerminator);
})()
,
// === 31. ses ./src/eval-scope.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_EVAL,create,defineProperties,freeze,assert;$h͏_imports([["./commons.js", [["FERAL_EVAL",[$h͏_a => (FERAL_EVAL = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);



const { Fail } = assert;

// We attempt to frustrate stack bumping attacks on the safe evaluator
// (`make-safe-evaluator.js`).
// A stack bumping attack forces an API call to throw a stack overflow
// `RangeError` at an inopportune time.
// The attacker arranges for the stack to be sufficiently deep that the API
// consumes exactly enough stack frames to throw an exception.
//
// For the safe evaluator, an exception thrown between adding and then deleting
// `eval` on `evalScope` could leak the real `eval` to an attacker's lexical
// scope.
// This would be sufficiently disastrous that we guard against it twice.
// First, we delete `eval` from `evalScope` immediately before rendering it to
// the guest program's lexical scope.
//
// If the attacker manages to arrange for `eval` to throw an exception after we
// call `allowNextEvalToBeUnsafe` but before the guest program accesses `eval`,
// it would be able to access `eval` once more in its own code.
// Although they could do no harm with a direct `eval`, they would be able to
// escape to the true global scope with an indirect `eval`.
//
//   prepareStack(depth, () => {
//     (eval)('');
//   });
//   const unsafeEval = (eval);
//   const safeEval = (eval);
//   const realGlobal = unsafeEval('globalThis');
//
// To protect against that case, we also delete `eval` from the `evalScope` in
// a `finally` block surrounding the call to the safe evaluator.
// The only way to reach this case is if `eval` remains on `evalScope` due to
// an attack, so we assume that attack would have have invalided our isolation
// and revoke all future access to the evaluator.
//
// To defeat a stack bumping attack, we must use fewer stack frames to recover
// in that `finally` block than we used in the `try` block.
// We have no reliable guarantees about how many stack frames a block of
// JavaScript will consume.
// Function inlining, tail-call optimization, variations in the size of a stack
// frame, and block scopes may affect the depth of the stack.
// The only number of acceptable stack frames to use in the finally block is
// zero.
// We only use property assignment and deletion in the safe evaluator's
// `finally` block.
// We use `delete evalScope.eval` to withhold the evaluator.
// We assign an envelope object over `evalScopeKit.revoked` to revoke the
// evaluator.
//
// This is why we supply a meaningfully named function for
// `allowNextEvalToBeUnsafe` but do not provide a corresponding
// `revokeAccessToUnsafeEval` or even simply `revoke`.
// These recovery routines are expressed inline in the safe evaluator.

       const makeEvalScopeKit = () => {
  const evalScope = create(null);
  const oneTimeEvalProperties = freeze({
    eval: {
      get() {
        delete evalScope.eval;
        return FERAL_EVAL;
      },
      enumerable: false,
      configurable: true,
    },
  });

  const evalScopeKit = {
    evalScope,
    allowNextEvalToBeUnsafe() {
      const { revoked } = evalScopeKit;
      if (revoked !== null) {
        Fail`a handler did not reset allowNextEvalToBeUnsafe ${revoked.err}`;
      }
      // Allow next reference to eval produce the unsafe FERAL_EVAL.
      // We avoid defineProperty because it consumes an extra stack frame taming
      // its return value.
      defineProperties(evalScope, oneTimeEvalProperties);
    },
    /** @type {null | { err: any }} */
    revoked: null,
  };

  return evalScopeKit;
};$h͏_once.makeEvalScopeKit(makeEvalScopeKit);
})()
,
// === 32. ses ./src/get-source-url.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_REG_EXP,regexpExec,stringSlice;$h͏_imports([["./commons.js", [["FERAL_REG_EXP",[$h͏_a => (FERAL_REG_EXP = $h͏_a)]],["regexpExec",[$h͏_a => (regexpExec = $h͏_a)]],["stringSlice",[$h͏_a => (stringSlice = $h͏_a)]]]]]);

// Captures a key and value of the form #key=value or @key=value
const sourceMetaEntryRegExp =
  '\\s*[@#]\\s*([a-zA-Z][a-zA-Z0-9]*)\\s*=\\s*([^\\s\\*]*)';
// Captures either a one-line or multi-line comment containing
// one #key=value or @key=value.
// Produces two pairs of capture groups, but the initial two may be undefined.
// On account of the mechanics of regular expressions, scanning from the end
// does not allow us to capture every pair, so getSourceURL must capture and
// trim until there are no matching comments.
const sourceMetaEntriesRegExp = new FERAL_REG_EXP(
  `(?:\\s*//${sourceMetaEntryRegExp}|/\\*${sourceMetaEntryRegExp}\\s*\\*/)\\s*$`,
);

/**
 * @param {string} src
 */
       const getSourceURL = src => {
  let sourceURL = '<unknown>';

  // Our regular expression matches the last one or two comments with key value
  // pairs at the end of the source, avoiding a scan over the entire length of
  // the string, but at the expense of being able to capture all the (key,
  // value) pair meta comments at the end of the source, which may include
  // sourceMapURL in addition to sourceURL.
  // So, we sublimate the comments out of the source until no source or no
  // comments remain.
  while (src.length > 0) {
    const match = regexpExec(sourceMetaEntriesRegExp, src);
    if (match === null) {
      break;
    }
    src = stringSlice(src, 0, src.length - match[0].length);

    // We skip $0 since it contains the entire match.
    // The match contains four capture groups,
    // two (key, value) pairs, the first of which
    // may be undefined.
    // On the off-chance someone put two sourceURL comments in their code with
    // different commenting conventions, the latter has precedence.
    if (match[3] === 'sourceURL') {
      sourceURL = match[4];
    } else if (match[1] === 'sourceURL') {
      sourceURL = match[2];
    }
  }

  return sourceURL;
};$h͏_once.getSourceURL(getSourceURL);
})()
,
// === 33. ses ./src/transforms.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_REG_EXP,SyntaxError,regexpReplace,sealRegexp,stringSearch,stringSlice,stringSplit,freeze,getSourceURL;$h͏_imports([["./commons.js", [["FERAL_REG_EXP",[$h͏_a => (FERAL_REG_EXP = $h͏_a)]],["SyntaxError",[$h͏_a => (SyntaxError = $h͏_a)]],["regexpReplace",[$h͏_a => (regexpReplace = $h͏_a)]],["sealRegexp",[$h͏_a => (sealRegexp = $h͏_a)]],["stringSearch",[$h͏_a => (stringSearch = $h͏_a)]],["stringSlice",[$h͏_a => (stringSlice = $h͏_a)]],["stringSplit",[$h͏_a => (stringSplit = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]]]],["./get-source-url.js", [["getSourceURL",[$h͏_a => (getSourceURL = $h͏_a)]]]]]);













/**
 * Find the first occurence of the given pattern and return
 * the location as the approximate line number.
 *
 * @param {string} src
 * @param {RegExp} pattern
 * @returns {number}
 */
function getLineNumber(src, pattern) {
  const index = stringSearch(src, pattern);
  if (index < 0) {
    return -1;
  }

  // The importPattern incidentally captures an initial \n in
  // an attempt to reject a . prefix, so we need to offset
  // the line number in that case.
  const adjustment = src[index] === '\n' ? 1 : 0;

  return stringSplit(stringSlice(src, 0, index), '\n').length + adjustment;
}

// /////////////////////////////////////////////////////////////////////////////

const htmlCommentPattern = sealRegexp(
  new FERAL_REG_EXP(`(?:${'<'}!--|--${'>'})`, 'g'),
);

/**
 * Conservatively reject the source text if it may contain text that some
 * JavaScript parsers may treat as an html-like comment. To reject without
 * parsing, `rejectHtmlComments` will also reject some other text as well.
 *
 * https://www.ecma-international.org/ecma-262/9.0/index.html#sec-html-like-comments
 * explains that JavaScript parsers may or may not recognize html
 * comment tokens "<" immediately followed by "!--" and "--"
 * immediately followed by ">" in non-module source text, and treat
 * them as a kind of line comment. Since otherwise both of these can
 * appear in normal JavaScript source code as a sequence of operators,
 * we have the terrifying possibility of the same source code parsing
 * one way on one correct JavaScript implementation, and another way
 * on another.
 *
 * This shim takes the conservative strategy of just rejecting source
 * text that contains these strings anywhere. Note that this very
 * source file is written strangely to avoid mentioning these
 * character strings explicitly.
 *
 * We do not write the regexp in a straightforward way, so that an
 * apparennt html comment does not appear in this file. Thus, we avoid
 * rejection by the overly eager rejectDangerousSources.
 *
 * @param {string} src
 * @returns {string}
 */
       const rejectHtmlComments = src => {
  const lineNumber = getLineNumber(src, htmlCommentPattern);
  if (lineNumber < 0) {
    return src;
  }
  const name = getSourceURL(src);
  // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_HTML_COMMENT_REJECTED.md
  throw SyntaxError(
    `Possible HTML comment rejected at ${name}:${lineNumber}. (SES_HTML_COMMENT_REJECTED)`,
  );
};

/**
 * An optional transform to place ahead of `rejectHtmlComments` to evade *that*
 * rejection. However, it may change the meaning of the program.
 *
 * This evasion replaces each alleged html comment with the space-separated
 * JavaScript operator sequence that it may mean, assuming that it appears
 * outside of a comment or literal string, in source code where the JS
 * parser makes no special case for html comments (like module source code).
 * In that case, this evasion preserves the meaning of the program, though it
 * does change the souce column numbers on each effected line.
 *
 * If the html comment appeared in a literal (a string literal, regexp literal,
 * or a template literal), then this evasion will change the meaning of the
 * program by changing the text of that literal.
 *
 * If the html comment appeared in a JavaScript comment, then this evasion does
 * not change the meaning of the program because it only changes the contents of
 * those comments.
 *
 * @param {string} src
 * @returns {string}
 */$h͏_once.rejectHtmlComments(rejectHtmlComments);
       const evadeHtmlCommentTest = src => {
  const replaceFn = match => (match[0] === '<' ? '< ! --' : '-- >');
  return regexpReplace(htmlCommentPattern, src, replaceFn);
};

// /////////////////////////////////////////////////////////////////////////////
$h͏_once.evadeHtmlCommentTest(evadeHtmlCommentTest);
const importPattern = sealRegexp(
  new FERAL_REG_EXP('(^|[^.]|\\.\\.\\.)\\bimport(\\s*(?:\\(|/[/*]))', 'g'),
);

/**
 * Conservatively reject the source text if it may contain a dynamic
 * import expression. To reject without parsing, `rejectImportExpressions` will
 * also reject some other text as well.
 *
 * The proposed dynamic import expression is the only syntax currently
 * proposed, that can appear in non-module JavaScript code, that
 * enables direct access to the outside world that cannot be
 * suppressed or intercepted without parsing and rewriting. Instead,
 * this shim conservatively rejects any source text that seems to
 * contain such an expression. To do this safely without parsing, we
 * must also reject some valid programs, i.e., those containing
 * apparent import expressions in literal strings or comments.
 *
 * The current conservative rule looks for the identifier "import"
 * followed by either an open paren or something that looks like the
 * beginning of a comment. We assume that we do not need to worry
 * about html comment syntax because that was already rejected by
 * rejectHtmlComments.
 *
 * this \s *must* match all kinds of syntax-defined whitespace. If e.g.
 * U+2028 (LINE SEPARATOR) or U+2029 (PARAGRAPH SEPARATOR) is treated as
 * whitespace by the parser, but not matched by /\s/, then this would admit
 * an attack like: import\u2028('power.js') . We're trying to distinguish
 * something like that from something like importnotreally('power.js') which
 * is perfectly safe.
 *
 * @param {string} src
 * @returns {string}
 */
       const rejectImportExpressions = src => {
  const lineNumber = getLineNumber(src, importPattern);
  if (lineNumber < 0) {
    return src;
  }
  const name = getSourceURL(src);
  // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_IMPORT_REJECTED.md
  throw SyntaxError(
    `Possible import expression rejected at ${name}:${lineNumber}. (SES_IMPORT_REJECTED)`,
  );
};

/**
 * An optional transform to place ahead of `rejectImportExpressions` to evade
 * *that* rejection. However, it may change the meaning of the program.
 *
 * This evasion replaces each suspicious `import` identifier with `__import__`.
 * If the alleged import expression appears in a JavaScript comment, this
 * evasion will not change the meaning of the program. If it appears in a
 * literal (string literal, regexp literal, or a template literal), then this
 * evasion will change the contents of that literal. If it appears as code
 * where it would be parsed as an expression, then it might or might not change
 * the meaning of the program, depending on the binding, if any, of the lexical
 * variable `__import__`.
 *
 * @param {string} src
 * @returns {string}
 */$h͏_once.rejectImportExpressions(rejectImportExpressions);
       const evadeImportExpressionTest = src => {
  const replaceFn = (_, p1, p2) => `${p1}__import__${p2}`;
  return regexpReplace(importPattern, src, replaceFn);
};

// /////////////////////////////////////////////////////////////////////////////
$h͏_once.evadeImportExpressionTest(evadeImportExpressionTest);
const someDirectEvalPattern = new FERAL_REG_EXP(
  '(^|[^.])\\beval(\\s*\\()',
  'g',
);

/**
 * Heuristically reject some text that seems to contain a direct eval
 * expression, with both false positives and false negavives. To reject without
 * parsing, `rejectSomeDirectEvalExpressions` may will also reject some other
 * text as well. It may also accept source text that contains a direct eval
 * written oddly, such as `(eval)(src)`. This false negative is not a security
 * vulnerability. Rather it is a compat hazard because it will execute as
 * an indirect eval under the SES-shim but as a direct eval on platforms that
 * support SES directly (like XS).
 *
 * The shim cannot correctly emulate a direct eval as explained at
 * https://github.com/Agoric/realms-shim/issues/12
 * If we did not reject direct eval syntax, we would
 * accidentally evaluate these with an emulation of indirect eval. To
 * prevent future compatibility problems, in shifting from use of the
 * shim to genuine platform support for the proposal, we should
 * instead statically reject code that seems to contain a direct eval
 * expression.
 *
 * As with the dynamic import expression, to avoid a full parse, we do
 * this approximately with a regexp, that will also reject strings
 * that appear safely in comments or strings. Unlike dynamic import,
 * if we miss some, this only creates future compat problems, not
 * security problems. Thus, we are only trying to catch innocent
 * occurrences, not malicious one. In particular, `(eval)(...)` is
 * direct eval syntax that would not be caught by the following regexp.
 *
 * Exported for unit tests.
 *
 * @param {string} src
 * @returns {string}
 */
       const rejectSomeDirectEvalExpressions = src => {
  const lineNumber = getLineNumber(src, someDirectEvalPattern);
  if (lineNumber < 0) {
    return src;
  }
  const name = getSourceURL(src);
  // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_EVAL_REJECTED.md
  throw SyntaxError(
    `Possible direct eval expression rejected at ${name}:${lineNumber}. (SES_EVAL_REJECTED)`,
  );
};

// /////////////////////////////////////////////////////////////////////////////

/**
 * A transform that bundles together the transforms that must unconditionally
 * happen last in order to ensure safe evaluation without parsing.
 *
 * @param {string} source
 * @returns {string}
 */$h͏_once.rejectSomeDirectEvalExpressions(rejectSomeDirectEvalExpressions);
       const mandatoryTransforms = source => {
  source = rejectHtmlComments(source);
  source = rejectImportExpressions(source);
  return source;
};

/**
 * Starting with `source`, apply each transform to the result of the
 * previous one, returning the result of the last transformation.
 *
 * @param {string} source
 * @param {((str: string) => string)[]} transforms
 * @returns {string}
 */$h͏_once.mandatoryTransforms(mandatoryTransforms);
       const applyTransforms = (source, transforms) => {
  for (let i = 0, l = transforms.length; i < l; i += 1) {
    const transform = transforms[i];
    source = transform(source);
  }
  return source;
};

// export all as a frozen object
$h͏_once.applyTransforms(applyTransforms);const transforms=freeze({
  rejectHtmlComments: freeze(rejectHtmlComments),
  evadeHtmlCommentTest: freeze(evadeHtmlCommentTest),
  rejectImportExpressions: freeze(rejectImportExpressions),
  evadeImportExpressionTest: freeze(evadeImportExpressionTest),
  rejectSomeDirectEvalExpressions: freeze(rejectSomeDirectEvalExpressions),
  mandatoryTransforms: freeze(mandatoryTransforms),
  applyTransforms: freeze(applyTransforms),
});$h͏_once.transforms(transforms);
})()
,
// === 34. ses ./src/scope-constants.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let arrayFilter,arrayIncludes,getOwnPropertyDescriptor,getOwnPropertyNames,hasOwn,regexpExec,Set,setHas;$h͏_imports([["./commons.js", [["arrayFilter",[$h͏_a => (arrayFilter = $h͏_a)]],["arrayIncludes",[$h͏_a => (arrayIncludes = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["getOwnPropertyNames",[$h͏_a => (getOwnPropertyNames = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]],["regexpExec",[$h͏_a => (regexpExec = $h͏_a)]],["Set",[$h͏_a => (Set = $h͏_a)]],["setHas",[$h͏_a => (setHas = $h͏_a)]]]]]);










/**
 * reservedNames
 * In JavaScript you cannot use reserved words as variable names (except for
 * "eval", which is specially reserved to prevent shadowing).
 * https://tc39.es/ecma262/multipage/ecmascript-language-lexical-grammar.html#sec-identifier-names
 */
const reservedNames = new Set([
  // 11.6.2.1 Keywords
  'await',
  'break',
  'case',
  'catch',
  'class',
  'const',
  'continue',
  'debugger',
  'default',
  'delete',
  'do',
  'else',
  'export',
  'extends',
  'finally',
  'for',
  'function',
  'if',
  'import',
  'in',
  'instanceof',
  'new',
  'return',
  'super',
  'switch',
  'this',
  'throw',
  'try',
  'typeof',
  'var',
  'void',
  'while',
  'with',
  'yield',

  // Also reserved when parsing strict mode code
  'let',
  'static',

  // 11.6.2.2 Future Reserved Words
  'enum',

  // Also reserved when parsing strict mode code
  'implements',
  'package',
  'protected',
  'interface',
  'private',
  'public',

  // Reserved but not mentioned in specs
  'await',

  'null',
  'true',
  'false',

  'this',
  'arguments',

  // Reserved by us
  'eval',
]);

/**
 * identifierPattern
 * Simplified validation of identifier names: may only contain alphanumeric
 * characters (or "$" or "_"), and may not start with a digit. This is safe
 * and does not reduces the compatibility of the shim. The motivation for
 * this limitation was to decrease the complexity of the implementation,
 * and to maintain a resonable level of performance.
 * Note: \w is equivalent [a-zA-Z_0-9]
 * See 11.6.1 Identifier Names
 */
const identifierPattern = /^[a-zA-Z_$][\w$]*$/;

/**
 * isValidIdentifierName()
 * Is a value allowed as an arbitrary identifier name?
 *
 * @param {string} name
 */
       const isValidIdentifierName = name =>
  !setHas(reservedNames, name) && !!regexpExec(identifierPattern, name);

/*
 * isImmutableDataProperty
 */$h͏_once.isValidIdentifierName(isValidIdentifierName);

function isImmutableDataProperty(obj, name) {
  const desc = getOwnPropertyDescriptor(obj, name);
  return (
    desc &&
    //
    // The getters will not have .writable, don't let the falsyness of
    // 'undefined' trick us: test with === false, not ! . However descriptors
    // inherit from the (potentially poisoned) global object, so we might see
    // extra properties which weren't really there. Accessor properties have
    // 'get/set/enumerable/configurable', while data properties have
    // 'value/writable/enumerable/configurable'.
    desc.configurable === false &&
    desc.writable === false &&
    //
    // Checks for data properties because they're the only ones we can
    // optimize (accessors are most likely non-constant). Descriptors can't
    // can't have accessors and value properties at the same time, therefore
    // this check is sufficient. Using explicit own property deal with the
    // case where Object.prototype has been poisoned.
    hasOwn(desc, 'value')
  );
}

/**
 * getScopeConstants()
 * What variable names might be brought into scope? These include all
 * property names which can be variable names, including the names
 * of inherited properties. It excludes symbols and names which are
 * keywords. We drop symbols safely. Currently, this shim refuses
 * service if any of the names are keywords or keyword-like. This is
 * safe and only affects performance optimization.
 *
 * @param {object} globalObject
 * @param {object} moduleLexicals
 */
       const getScopeConstants = (globalObject, moduleLexicals = {}) => {
  // getOwnPropertyNames() does ignore Symbols so we don't need to
  // filter them out.
  const globalObjectNames = getOwnPropertyNames(globalObject);
  const moduleLexicalNames = getOwnPropertyNames(moduleLexicals);

  // Collect all valid & immutable identifiers from the endowments.
  const moduleLexicalConstants = arrayFilter(
    moduleLexicalNames,
    name =>
      isValidIdentifierName(name) &&
      isImmutableDataProperty(moduleLexicals, name),
  );

  // Collect all valid & immutable identifiers from the global that
  // are also not present in the endowments (immutable or not).
  const globalObjectConstants = arrayFilter(
    globalObjectNames,
    name =>
      // Can't define a constant: it would prevent a
      // lookup on the endowments.
      !arrayIncludes(moduleLexicalNames, name) &&
      isValidIdentifierName(name) &&
      isImmutableDataProperty(globalObject, name),
  );

  return {
    globalObjectConstants,
    moduleLexicalConstants,
  };
};$h͏_once.getScopeConstants(getScopeConstants);
})()
,
// === 35. ses ./src/make-evaluate.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_FUNCTION,arrayJoin,apply,getScopeConstants;$h͏_imports([["./commons.js", [["FERAL_FUNCTION",[$h͏_a => (FERAL_FUNCTION = $h͏_a)]],["arrayJoin",[$h͏_a => (arrayJoin = $h͏_a)]],["apply",[$h͏_a => (apply = $h͏_a)]]]],["./scope-constants.js", [["getScopeConstants",[$h͏_a => (getScopeConstants = $h͏_a)]]]]]);




/**
 * buildOptimizer()
 * Given an array of identifiers, the optimizer returns a `const` declaration
 * destructuring `this.${name}`.
 *
 * @param {Array<string>} constants
 * @param {string} name
 */
function buildOptimizer(constants, name) {
  // No need to build an optimizer when there are no constants.
  if (constants.length === 0) return '';
  // Use 'this' to avoid going through the scope proxy, which is unnecessary
  // since the optimizer only needs references to the safe global.
  // Destructure the constants from the target scope object.
  return `const {${arrayJoin(constants, ',')}} = this.${name};`;
}

/**
 * makeEvaluate()
 * Create an 'evaluate' function with the correct optimizer inserted.
 *
 * @param {object} context
 * @param {object} context.evalScope
 * @param {object} context.moduleLexicals
 * @param {object} context.globalObject
 * @param {object} context.scopeTerminator
 */
       const makeEvaluate = context => {
  const { globalObjectConstants, moduleLexicalConstants } = getScopeConstants(
    context.globalObject,
    context.moduleLexicals,
  );
  const globalObjectOptimizer = buildOptimizer(
    globalObjectConstants,
    'globalObject',
  );
  const moduleLexicalOptimizer = buildOptimizer(
    moduleLexicalConstants,
    'moduleLexicals',
  );

  // Create a function in sloppy mode, so that we can use 'with'. It returns
  // a function in strict mode that evaluates the provided code using direct
  // eval, and thus in strict mode in the same scope. We must be very careful
  // to not create new names in this scope

  // 1: we use multiple nested 'with' to catch all free variable names. The
  // `this` value of the outer sloppy function holds the different scope
  // layers, from inner to outer:
  //    a) `evalScope` which must release the `FERAL_EVAL` as 'eval' once for
  //       every invocation of the inner `evaluate` function in order to
  //       trigger direct eval. The direct eval semantics is what allows the
  //       evaluated code to lookup free variable names on the other scope
  //       objects and not in global scope.
  //    b) `moduleLexicals` which provide a way to introduce free variables
  //       that are not available on the globalObject.
  //    c) `globalObject` is the global scope object of the evaluator, aka the
  //       Compartment's `globalThis`.
  //    d) `scopeTerminator` is a proxy object which prevents free variable
  //       lookups to escape to the start compartment's global object.
  // 2: `optimizer`s catch constant variable names for speed.
  // 3: The inner strict `evaluate` function should be passed two parameters:
  //    a) its arguments[0] is the source to be directly evaluated.
  //    b) its 'this' is the this binding seen by the code being
  //       directly evaluated (the globalObject).

  // Notes:
  // - The `optimizer` strings only lookup values on the `globalObject` and
  //   `moduleLexicals` objects by construct. Keywords like 'function' are
  //   reserved and cannot be used as a variable, so they are excluded from the
  //   optimizer. Furthermore to prevent shadowing 'eval', while a valid
  //   identifier, that name is also explicitly excluded.
  // - when 'eval' is looked up in the `evalScope`, the powerful unsafe eval
  //   intrinsic is returned after automatically removing it from the
  //   `evalScope`. Any further reference to 'eval' in the evaluate string will
  //   get the tamed evaluator from the `globalObject`, if any.

  // TODO https://github.com/endojs/endo/issues/816
  // The optimizer currently runs under sloppy mode, and although we doubt that
  // there is any vulnerability introduced just by running the optimizer
  // sloppy, we are much more confident in the semantics of strict mode.
  // The `evaluate` function can be and is reused across multiple evaluations.
  // Since the optimizer should not be re-evaluated every time, it cannot be
  // inside the `evaluate` closure. While we could potentially nest an
  // intermediate layer of `() => {'use strict'; ${optimizers}; ...`, it
  // doesn't seem worth the overhead and complexity.
  const evaluateFactory = FERAL_FUNCTION(`
    with (this.scopeTerminator) {
      with (this.globalObject) {
        with (this.moduleLexicals) {
          with (this.evalScope) {
            ${globalObjectOptimizer}
            ${moduleLexicalOptimizer}
            return function() {
              'use strict';
              return eval(arguments[0]);
            };
          }
        }
      }
    }
  `);

  return apply(evaluateFactory, context, []);
};$h͏_once.makeEvaluate(makeEvaluate);
})()
,
// === 36. ses ./src/make-safe-evaluator.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let apply,arrayFlatMap,freeze,identity,strictScopeTerminator,createSloppyGlobalsScopeTerminator,makeEvalScopeKit,applyTransforms,mandatoryTransforms,makeEvaluate,assert;$h͏_imports([["./commons.js", [["apply",[$h͏_a => (apply = $h͏_a)]],["arrayFlatMap",[$h͏_a => (arrayFlatMap = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["identity",[$h͏_a => (identity = $h͏_a)]]]],["./strict-scope-terminator.js", [["strictScopeTerminator",[$h͏_a => (strictScopeTerminator = $h͏_a)]]]],["./sloppy-globals-scope-terminator.js", [["createSloppyGlobalsScopeTerminator",[$h͏_a => (createSloppyGlobalsScopeTerminator = $h͏_a)]]]],["./eval-scope.js", [["makeEvalScopeKit",[$h͏_a => (makeEvalScopeKit = $h͏_a)]]]],["./transforms.js", [["applyTransforms",[$h͏_a => (applyTransforms = $h͏_a)]],["mandatoryTransforms",[$h͏_a => (mandatoryTransforms = $h͏_a)]]]],["./make-evaluate.js", [["makeEvaluate",[$h͏_a => (makeEvaluate = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);










const { Fail } = assert;

/**
 * makeSafeEvaluator()
 * Build the low-level operation used by all evaluators:
 * eval(), Function(), Compartment.prototype.evaluate().
 *
 * @param {object} options
 * @param {object} options.globalObject
 * @param {object} [options.moduleLexicals]
 * @param {Array<import('./lockdown.js').Transform>} [options.globalTransforms]
 * @param {boolean} [options.sloppyGlobalsMode]
 */
       const makeSafeEvaluator = ({
  globalObject,
  moduleLexicals = {},
  globalTransforms = [],
  sloppyGlobalsMode = false,
}) => {
  const scopeTerminator = sloppyGlobalsMode
    ? createSloppyGlobalsScopeTerminator(globalObject)
    : strictScopeTerminator;
  const evalScopeKit = makeEvalScopeKit();
  const { evalScope } = evalScopeKit;

  const evaluateContext = freeze({
    evalScope,
    moduleLexicals,
    globalObject,
    scopeTerminator,
  });

  // Defer creating the actual evaluator to first use.
  // Creating a compartment should be possible in no-eval environments
  // It also allows more global constants to be captured by the optimizer
  let evaluate;
  const provideEvaluate = () => {
    if (!evaluate) {
      evaluate = makeEvaluate(evaluateContext);
    }
  };

  /**
   * @param {string} source
   * @param {object} [options]
   * @param {Array<import('./lockdown.js').Transform>} [options.localTransforms]
   */
  const safeEvaluate = (source, options) => {
    const { localTransforms = [] } = options || {};
    provideEvaluate();

    // Execute the mandatory transforms last to ensure that any rewritten code
    // meets those mandatory requirements.
    source = applyTransforms(
      source,
      arrayFlatMap(
        [localTransforms, globalTransforms, [mandatoryTransforms]],
        identity,
      ),
    );

    let err;
    try {
      // Allow next reference to eval produce the unsafe FERAL_EVAL.
      // eslint-disable-next-line @endo/no-polymorphic-call
      evalScopeKit.allowNextEvalToBeUnsafe();

      // Ensure that "this" resolves to the safe global.
      return apply(evaluate, globalObject, [source]);
    } catch (e) {
      // stash the child-code error in hopes of debugging the internal failure
      err = e;
      throw e;
    } finally {
      const unsafeEvalWasStillExposed = 'eval' in evalScope;
      delete evalScope.eval;
      if (unsafeEvalWasStillExposed) {
        // Barring a defect in the SES shim, the evalScope should allow the
        // powerful, unsafe  `eval` to be used by `evaluate` exactly once, as the
        // very first name that it attempts to access from the lexical scope.
        // A defect in the SES shim could throw an exception after we set
        // `evalScope.eval` and before `evaluate` calls `eval` internally.
        // If we get here, SES is very broken.
        // This condition is one where this vat is now hopelessly confused, and
        // the vat as a whole should be aborted.
        // No further code should run.
        // All immediately reachable state should be abandoned.
        // However, that is not yet possible, so we at least prevent further
        // variable resolution via the scopeHandler, and throw an error with
        // diagnostic info including the thrown error if any from evaluating the
        // source code.
        evalScopeKit.revoked = { err };
        // TODO A GOOD PLACE TO PANIC(), i.e., kill the vat incarnation.
        // See https://github.com/Agoric/SES-shim/issues/490
        Fail`handler did not reset allowNextEvalToBeUnsafe ${err}`;
      }
    }
  };

  return { safeEvaluate };
};$h͏_once.makeSafeEvaluator(makeSafeEvaluator);
})()
,
// === 37. ses ./src/tame-function-tostring.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let WeakSet,defineProperty,freeze,functionPrototype,functionToString,stringEndsWith,weaksetAdd,weaksetHas;$h͏_imports([["./commons.js", [["WeakSet",[$h͏_a => (WeakSet = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["functionPrototype",[$h͏_a => (functionPrototype = $h͏_a)]],["functionToString",[$h͏_a => (functionToString = $h͏_a)]],["stringEndsWith",[$h͏_a => (stringEndsWith = $h͏_a)]],["weaksetAdd",[$h͏_a => (weaksetAdd = $h͏_a)]],["weaksetHas",[$h͏_a => (weaksetHas = $h͏_a)]]]]]);










const nativeSuffix = ') { [native code] }';

// Note: Top level mutable state. Does not make anything worse, since the
// patching of `Function.prototype.toString` is also globally stateful. We
// use this top level state so that multiple calls to `tameFunctionToString` are
// idempotent, rather than creating redundant indirections.
let markVirtualizedNativeFunction;

/**
 * Replace `Function.prototype.toString` with one that recognizes
 * shimmed functions as honorary native functions.
 */
       const tameFunctionToString = () => {
  if (markVirtualizedNativeFunction === undefined) {
    const virtualizedNativeFunctions = new WeakSet();

    const tamingMethods = {
      toString() {
        const str = functionToString(this);
        if (
          stringEndsWith(str, nativeSuffix) ||
          !weaksetHas(virtualizedNativeFunctions, this)
        ) {
          return str;
        }
        return `function ${this.name}() { [native code] }`;
      },
    };

    defineProperty(functionPrototype, 'toString', {
      value: tamingMethods.toString,
    });

    markVirtualizedNativeFunction = freeze(func =>
      weaksetAdd(virtualizedNativeFunctions, func),
    );
  }
  return markVirtualizedNativeFunction;
};$h͏_once.tameFunctionToString(tameFunctionToString);
})()
,
// === 38. ses ./src/tame-domains.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let TypeError,globalThis,getOwnPropertyDescriptor,defineProperty;$h͏_imports([["./commons.js", [["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]]]]]);Object.defineProperty(tameDomains,'name',{value:"tameDomains"});$h͏_once.tameDomains(tameDomains);








       function tameDomains(domainTaming = 'safe') {
  if (domainTaming === 'unsafe') {
    return;
  }

  // Protect against the hazard presented by Node.js domains.
  const globalProcess = globalThis.process || undefined;
  if (typeof globalProcess === 'object') {
    // Check whether domains were initialized.
    const domainDescriptor = getOwnPropertyDescriptor(globalProcess, 'domain');
    if (domainDescriptor !== undefined && domainDescriptor.get !== undefined) {
      // The domain descriptor on Node.js initially has value: null, which
      // becomes a get, set pair after domains initialize.
      // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_NO_DOMAINS.md
      throw TypeError(
        `SES failed to lockdown, Node.js domains have been initialized (SES_NO_DOMAINS)`,
      );
    }
    // Prevent domains from initializing.
    // This is clunky because the exception thrown from the domains package does
    // not direct the user's gaze toward a knowledge base about the problem.
    // The domain module merely throws an exception when it attempts to define
    // the domain property of the process global during its initialization.
    // We have no better recourse because Node.js uses defineProperty too.
    defineProperty(globalProcess, 'domain', {
      value: null,
      configurable: false,
      writable: false,
      enumerable: false,
    });
  }
}
})()
,
// === 39. ses ./src/tame-module-source.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let functionPrototype,getPrototypeOf,globalThis,objectPrototype,setPrototypeOf;$h͏_imports([["./commons.js", [["functionPrototype",[$h͏_a => (functionPrototype = $h͏_a)]],["getPrototypeOf",[$h͏_a => (getPrototypeOf = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["objectPrototype",[$h͏_a => (objectPrototype = $h͏_a)]],["setPrototypeOf",[$h͏_a => (setPrototypeOf = $h͏_a)]]]]]);







       const tameModuleSource = () => {
  const newIntrinsics = {};

  const ModuleSource = globalThis.ModuleSource;
  if (ModuleSource !== undefined) {
    newIntrinsics.ModuleSource = ModuleSource;

    // We introduce ModuleSource.[[Proto]] === AbstractModuleSource
    // and ModuleSource.prototype.[[Proto]] === AbstractModuleSource.prototype
    // if that layer is absent because the permitting system can more
    // gracefully tolerate the absence of an expected prototype than the
    // presence of an unexpected prototype,.
    function AbstractModuleSource() {
      // no-op safe to super()
    }

    const ModuleSourceProto = getPrototypeOf(ModuleSource);
    if (ModuleSourceProto === functionPrototype) {
      setPrototypeOf(ModuleSource, AbstractModuleSource);
      newIntrinsics['%AbstractModuleSource%'] = AbstractModuleSource;
      newIntrinsics['%AbstractModuleSourcePrototype%'] =
        AbstractModuleSource.prototype;
    } else {
      newIntrinsics['%AbstractModuleSource%'] = ModuleSourceProto;
      newIntrinsics['%AbstractModuleSourcePrototype%'] =
        ModuleSourceProto.prototype;
    }

    const ModuleSourcePrototype = ModuleSource.prototype;
    if (ModuleSourcePrototype !== undefined) {
      newIntrinsics['%ModuleSourcePrototype%'] = ModuleSourcePrototype;

      // ModuleSource.prototype.__proto__ should be the
      // AbstractModuleSource.prototype.
      const ModuleSourcePrototypeProto = getPrototypeOf(ModuleSourcePrototype);
      if (ModuleSourcePrototypeProto === objectPrototype) {
        setPrototypeOf(ModuleSource.prototype, AbstractModuleSource.prototype);
      }
    }
  }

  return newIntrinsics;
};$h͏_once.tameModuleSource(tameModuleSource);
})()
,
// === 40. ses ./src/error/console.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let WeakSet,arrayFilter,arrayFlatMap,arrayMap,arrayPop,arrayPush,defineProperty,freeze,fromEntries,isError,stringEndsWith,stringIncludes,stringSplit,weaksetAdd,weaksetHas;$h͏_imports([["../commons.js", [["WeakSet",[$h͏_a => (WeakSet = $h͏_a)]],["arrayFilter",[$h͏_a => (arrayFilter = $h͏_a)]],["arrayFlatMap",[$h͏_a => (arrayFlatMap = $h͏_a)]],["arrayMap",[$h͏_a => (arrayMap = $h͏_a)]],["arrayPop",[$h͏_a => (arrayPop = $h͏_a)]],["arrayPush",[$h͏_a => (arrayPush = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["fromEntries",[$h͏_a => (fromEntries = $h͏_a)]],["isError",[$h͏_a => (isError = $h͏_a)]],["stringEndsWith",[$h͏_a => (stringEndsWith = $h͏_a)]],["stringIncludes",[$h͏_a => (stringIncludes = $h͏_a)]],["stringSplit",[$h͏_a => (stringSplit = $h͏_a)]],["weaksetAdd",[$h͏_a => (weaksetAdd = $h͏_a)]],["weaksetHas",[$h͏_a => (weaksetHas = $h͏_a)]]]]]);
























/**
 * @import {FilterConsole, LogSeverity, VirtualConsole} from './types.js'
 * @import {ErrorInfo, ErrorInfoKind, LogRecord, NoteCallback, LoggedErrorHandler, MakeCausalConsole, MakeLoggingConsoleKit} from "./internal-types.js";
 */

/**
 * Explicitly set a function's name, supporting use of arrow functions for which
 * source text doesn't include a name and no initial name is set by
 * NamedEvaluation
 * https://tc39.es/ecma262/multipage/syntax-directed-operations.html#sec-runtime-semantics-namedevaluation
 * Instead, we hope that tooling uses only the explicit `name` property.
 *
 * @template {Function} F
 * @param {string} name
 * @param {F} fn
 * @returns {F}
 */
const defineName = (name, fn) => defineProperty(fn, 'name', { value: name });

// For our internal debugging purposes, uncomment
// const internalDebugConsole = console;

// The permitted console methods, from:
// Whatwg "living standard" https://console.spec.whatwg.org/
// Node https://nodejs.org/dist/latest-v14.x/docs/api/console.html
// MDN https://developer.mozilla.org/en-US/docs/Web/API/Console_API
// TypeScript https://openstapps.gitlab.io/projectmanagement/interfaces/_node_modules__types_node_globals_d_.console.html
// Chrome https://developers.google.com/web/tools/chrome-devtools/console/api

// All console level methods have parameters (fmt?, ...args)
// where the argument sequence `fmt?, ...args` formats args according to
// fmt if fmt is a format string. Otherwise, it just renders them all as values
// separated by spaces.
// https://console.spec.whatwg.org/#formatter
// https://nodejs.org/docs/latest/api/util.html#util_util_format_format_args

// For the causal console, all occurrences of `fmt, ...args` or `...args` by
// itself must check for the presence of an error to ask the
// `loggedErrorHandler` to handle.
// In theory we should do a deep inspection to detect for example an array
// containing an error. We currently do not detect these and may never.

/** @typedef {keyof VirtualConsole | 'profile' | 'profileEnd'} ConsoleProps */

/**
 * Those console methods whose actual parameters are `(fmt?, ...args)`
 * even if their TypeScript types claim otherwise.
 *
 * Each is paired with what we consider to be their log severity level.
 * This is the same as the log severity of these on other
 * platform console implementations when they all agree.
 *
 * @type {readonly [ConsoleProps, LogSeverity | undefined][]}
 */
       const consoleLevelMethods = freeze([
  ['debug', 'debug'], // (fmt?, ...args) verbose level on Chrome
  ['log', 'log'], // (fmt?, ...args) info level on Chrome
  ['info', 'info'], // (fmt?, ...args)
  ['warn', 'warn'], // (fmt?, ...args)
  ['error', 'error'], // (fmt?, ...args)

  ['trace', 'log'], // (fmt?, ...args)
  ['dirxml', 'log'], // (fmt?, ...args)          but TS typed (...data)
  ['group', 'log'], // (fmt?, ...args)           but TS typed (...label)
  ['groupCollapsed', 'log']  // (fmt?, ...args)  but TS typed (...label)
]);

/**
 * Those console methods other than those already enumerated by
 * `consoleLevelMethods`.
 *
 * Each is paired with what we consider to be their log severity level.
 * This is the same as the log severity of these on other
 * platform console implementations when they all agree.
 *
 * @type {readonly [ConsoleProps, LogSeverity | undefined][]}
 */$h͏_once.consoleLevelMethods(consoleLevelMethods);
       const consoleOtherMethods = freeze([
  ['assert', 'error'], // (value, fmt?, ...args)
  ['timeLog', 'log'], // (label?, ...args) no fmt string

  // Insensitive to whether any argument is an error. All arguments can pass
  // thru to baseConsole as is.
  ['clear', undefined], // ()
  ['count', 'info'], // (label?)
  ['countReset', undefined], // (label?)
  ['dir', 'log'], // (item, options?)
  ['groupEnd', 'log'], // ()
  // In theory tabular data may be or contain an error. However, we currently
  // do not detect these and may never.
  ['table', 'log'], // (tabularData, properties?)
  ['time', 'info'], // (label?)
  ['timeEnd', 'info'], // (label?)

  // Node Inspector only, MDN, and TypeScript, but not whatwg
  ['profile', undefined], // (label?)
  ['profileEnd', undefined], // (label?)
  ['timeStamp', undefined]  // (label?)
]);

/** @type {readonly [ConsoleProps, LogSeverity | undefined][]} */$h͏_once.consoleOtherMethods(consoleOtherMethods);
const consoleMethodPermits = freeze([
  ...consoleLevelMethods,
  ...consoleOtherMethods,
]);

/**
 * consoleOmittedProperties is currently unused. I record and maintain it here
 * with the intention that it be treated like the `false` entries in the main
 * SES permits: that seeing these on the original console is expected, but
 * seeing anything else that's outside the permits is surprising and should
 * provide a diagnostic.
 *
 * const consoleOmittedProperties = freeze([
 *   'memory', // Chrome
 *   'exception', // FF, MDN
 *   '_ignoreErrors', // Node
 *   '_stderr', // Node
 *   '_stderrErrorHandler', // Node
 *   '_stdout', // Node
 *   '_stdoutErrorHandler', // Node
 *   '_times', // Node
 *   'context', // Chrome, Node
 *   'record', // Safari
 *   'recordEnd', // Safari
 *
 *   'screenshot', // Safari
 *   // Symbols
 *   '@@toStringTag', // Chrome: "Object", Safari: "Console"
 *   // A variety of other symbols also seen on Node
 * ]);
 */

// //////////////////////////// Logging Console ////////////////////////////////

/** @type {MakeLoggingConsoleKit} */
       const makeLoggingConsoleKit = (
  loggedErrorHandler,
  { shouldResetForDebugging = false } = {},
) => {
  if (shouldResetForDebugging) {
    // eslint-disable-next-line @endo/no-polymorphic-call
    loggedErrorHandler.resetErrorTagNum();
  }

  // Not frozen!
  let logArray = [];

  const loggingConsole = fromEntries(
    arrayMap(consoleMethodPermits, ([name, _]) => {
      /**
       * @param {...any} args
       */
      const method = defineName(name, (...args) => {
        arrayPush(logArray, [name, ...args]);
      });
      return [name, freeze(method)];
    }),
  );
  freeze(loggingConsole);

  const takeLog = () => {
    const result = freeze(logArray);
    logArray = [];
    return result;
  };
  freeze(takeLog);

  const typedLoggingConsole = /** @type {VirtualConsole} */ (loggingConsole);

  return freeze({ loggingConsole: typedLoggingConsole, takeLog });
};$h͏_once.makeLoggingConsoleKit(makeLoggingConsoleKit);
freeze(makeLoggingConsoleKit);

/**
 * Makes the same calls on a `baseConsole` that were made on a
 * `loggingConsole` to produce this `log`. In this way, a logging console
 * can be used as a buffer to delay the application of these calls to a
 * `baseConsole`.
 *
 * @param {LogRecord[]} log
 * @param {VirtualConsole} baseConsole
 */
       const pumpLogToConsole = (log, baseConsole) => {
  for (const [name, ...args] of log) {
    // eslint-disable-next-line @endo/no-polymorphic-call
    baseConsole[name](...args);
  }
};
// //////////////////////////// Causal Console /////////////////////////////////

/** @type {ErrorInfo} */$h͏_once.pumpLogToConsole(pumpLogToConsole);
const ErrorInfo = {
  NOTE: 'ERROR_NOTE:',
  MESSAGE: 'ERROR_MESSAGE:',
  CAUSE: 'cause:',
  ERRORS: 'errors:',
};
freeze(ErrorInfo);

/** @type {MakeCausalConsole} */
       const makeCausalConsole = (baseConsole, loggedErrorHandler) => {
  if (!baseConsole) {
    return undefined;
  }

  const { getStackString, tagError, takeMessageLogArgs, takeNoteLogArgsArray } =
    loggedErrorHandler;

  /**
   * @param {ReadonlyArray<any>} logArgs
   * @param {Array<any>} subErrorsSink
   * @returns {any}
   */
  const extractErrorArgs = (logArgs, subErrorsSink) => {
    const argTags = arrayMap(logArgs, arg => {
      if (isError(arg)) {
        arrayPush(subErrorsSink, arg);
        return `(${tagError(arg)})`;
      }
      return arg;
    });
    return argTags;
  };

  /**
   * @param {LogSeverity} severity
   * @param {Error} error
   * @param {ErrorInfoKind} kind
   * @param {readonly any[]} logArgs
   * @param {Array<Error>} subErrorsSink
   */
  const logErrorInfo = (severity, error, kind, logArgs, subErrorsSink) => {
    const errorTag = tagError(error);
    const errorName =
      kind === ErrorInfo.MESSAGE ? `${errorTag}:` : `${errorTag} ${kind}`;
    const argTags = extractErrorArgs(logArgs, subErrorsSink);
    // eslint-disable-next-line @endo/no-polymorphic-call
    baseConsole[severity](errorName, ...argTags);
  };

  /**
   * Logs the `subErrors` within a group name mentioning `optTag`.
   *
   * @param {LogSeverity} severity
   * @param {Error[]} subErrors
   * @param {string | undefined} optTag
   * @returns {void}
   */
  const logSubErrors = (severity, subErrors, optTag = undefined) => {
    if (subErrors.length === 0) {
      return;
    }
    if (subErrors.length === 1 && optTag === undefined) {
      // eslint-disable-next-line no-use-before-define
      logError(severity, subErrors[0]);
      return;
    }
    let label;
    if (subErrors.length === 1) {
      label = `Nested error`;
    } else {
      label = `Nested ${subErrors.length} errors`;
    }
    if (optTag !== undefined) {
      label = `${label} under ${optTag}`;
    }
    // eslint-disable-next-line @endo/no-polymorphic-call
    baseConsole.group(label);
    try {
      for (const subError of subErrors) {
        // eslint-disable-next-line no-use-before-define
        logError(severity, subError);
      }
    } finally {
      if (baseConsole.groupEnd) {
        // eslint-disable-next-line @endo/no-polymorphic-call
        baseConsole.groupEnd();
      }
    }
  };

  const errorsLogged = new WeakSet();

  /** @type {(severity: LogSeverity) => NoteCallback} */
  const makeNoteCallback = severity => (error, noteLogArgs) => {
    const subErrors = [];
    // Annotation arrived after the error has already been logged,
    // so just log the annotation immediately, rather than remembering it.
    logErrorInfo(severity, error, ErrorInfo.NOTE, noteLogArgs, subErrors);
    logSubErrors(severity, subErrors, tagError(error));
  };

  /**
   * @param {LogSeverity} severity
   * @param {Error} error
   */
  const logError = (severity, error) => {
    if (weaksetHas(errorsLogged, error)) {
      return;
    }
    const errorTag = tagError(error);
    weaksetAdd(errorsLogged, error);
    const subErrors = [];
    const messageLogArgs = takeMessageLogArgs(error);
    const noteLogArgsArray = takeNoteLogArgsArray(
      error,
      makeNoteCallback(severity),
    );
    // Show the error's most informative error message
    if (messageLogArgs === undefined) {
      // If there is no message log args, then just show the message that
      // the error itself carries.
      // eslint-disable-next-line @endo/no-polymorphic-call
      baseConsole[severity](`${errorTag}:`, error.message);
    } else {
      // If there is one, we take it to be strictly more informative than the
      // message string carried by the error, so show it *instead*.
      logErrorInfo(
        severity,
        error,
        ErrorInfo.MESSAGE,
        messageLogArgs,
        subErrors,
      );
    }
    // After the message but before any other annotations, show the stack.
    let stackString = getStackString(error);
    if (
      typeof stackString === 'string' &&
      stackString.length >= 1 &&
      !stringEndsWith(stackString, '\n')
    ) {
      stackString += '\n';
    }
    // eslint-disable-next-line @endo/no-polymorphic-call
    baseConsole[severity](stackString);
    // Show the other annotations on error
    if (error.cause) {
      logErrorInfo(severity, error, ErrorInfo.CAUSE, [error.cause], subErrors);
    }
    // @ts-expect-error AggregateError has an `errors` property.
    if (error.errors) {
      // @ts-expect-error AggregateError has an `errors` property.
      logErrorInfo(severity, error, ErrorInfo.ERRORS, error.errors, subErrors);
    }
    for (const noteLogArgs of noteLogArgsArray) {
      logErrorInfo(severity, error, ErrorInfo.NOTE, noteLogArgs, subErrors);
    }
    // explain all the errors seen in the messages already emitted.
    logSubErrors(severity, subErrors, errorTag);
  };

  const levelMethods = arrayMap(consoleLevelMethods, ([level, _]) => {
    /**
     * @param {...any} logArgs
     */
    const levelMethod = defineName(level, (...logArgs) => {
      const subErrors = [];
      const argTags = extractErrorArgs(logArgs, subErrors);
      if (baseConsole[level]) {
        // eslint-disable-next-line @endo/no-polymorphic-call
        baseConsole[level](...argTags);
      }
      // @ts-expect-error ConsoleProp vs LogSeverity mismatch
      logSubErrors(level, subErrors);
    });
    return [level, freeze(levelMethod)];
  });
  const otherMethodNames = arrayFilter(
    consoleOtherMethods,
    ([name, _]) => name in baseConsole,
  );
  const otherMethods = arrayMap(otherMethodNames, ([name, _]) => {
    /**
     * @param {...any} args
     */
    const otherMethod = defineName(name, (...args) => {
      // @ts-ignore
      // eslint-disable-next-line @endo/no-polymorphic-call
      baseConsole[name](...args);
      return undefined;
    });
    return [name, freeze(otherMethod)];
  });

  const causalConsole = fromEntries([...levelMethods, ...otherMethods]);
  return /** @type {VirtualConsole} */ (freeze(causalConsole));
};$h͏_once.makeCausalConsole(makeCausalConsole);
freeze(makeCausalConsole);

/**
 * @typedef {(...args: unknown[]) => void} Logger
 */

/**
 * This is a rather horrible kludge to indent the output to a logger in
 * the case where some arguments are strings containing newlines. Part of
 * the problem is that console-like loggers, including the one in ava,
 * join the string arguments of the log message with a space.
 * Because of this, there's an extra space at the beginning of each of
 * the split lines. So this kludge compensated by putting an extra empty
 * string at the beginning, so that the logger will add the same extra
 * joiner.
 * TODO: Fix this horrible kludge, and indent in a sane manner.
 *
 * @param {string} str
 * @param {string} sep
 * @param {string[]} indents
 * @returns {string[]}
 */
const indentAfterAllSeps = (str, sep, indents) => {
  const [firstLine, ...restLines] = stringSplit(str, sep);
  const indentedRest = arrayFlatMap(restLines, line => [sep, ...indents, line]);
  return ['', firstLine, ...indentedRest];
};

/**
 * @param {LoggedErrorHandler} loggedErrorHandler
 */
       const defineCausalConsoleFromLogger = loggedErrorHandler => {
  /**
   * Implement the `VirtualConsole` API badly by turning all calls into
   * calls on `tlogger`. We need to do this to have `console` logging
   * turn into calls to Ava's `t.log`, so these console log messages
   * are output in the right place.
   *
   * @param {Logger} tlogger
   * @returns {VirtualConsole}
   */
  const makeCausalConsoleFromLogger = tlogger => {
    const indents = [];
    const logWithIndent = (...args) => {
      if (indents.length > 0) {
        args = arrayFlatMap(args, arg =>
          typeof arg === 'string' && stringIncludes(arg, '\n')
            ? indentAfterAllSeps(arg, '\n', indents)
            : [arg],
        );
        args = [...indents, ...args];
      }
      return tlogger(...args);
    };

    const baseConsole = fromEntries([
      ...arrayMap(consoleLevelMethods, ([name]) => [
        name,
        defineName(name, (...args) => logWithIndent(...args)),
      ]),
      ...arrayMap(consoleOtherMethods, ([name]) => [
        name,
        defineName(name, (...args) => logWithIndent(name, ...args)),
      ]),
    ]);
    // https://console.spec.whatwg.org/#grouping
    for (const name of ['group', 'groupCollapsed']) {
      if (baseConsole[name]) {
        baseConsole[name] = defineName(name, (...args) => {
          if (args.length >= 1) {
            // Prefix the logged data with "group" or "groupCollapsed".
            logWithIndent(...args);
          }
          // A single space is enough;
          // the host console will separate them with additional spaces.
          arrayPush(indents, ' ');
        });
      } else {
        baseConsole[name] = defineName(name, () => {});
      }
    }
    baseConsole.groupEnd = defineName(
      'groupEnd',
      baseConsole.groupEnd
        ? (...args) => {
            arrayPop(indents);
          }
        : () => {},
    );
    harden(baseConsole);
    const causalConsole = makeCausalConsole(
      /** @type {VirtualConsole} */ (baseConsole),
      loggedErrorHandler,
    );
    return /** @type {VirtualConsole} */ (causalConsole);
  };
  return freeze(makeCausalConsoleFromLogger);
};$h͏_once.defineCausalConsoleFromLogger(defineCausalConsoleFromLogger);
freeze(defineCausalConsoleFromLogger);

// ///////////////////////// Filter Console ////////////////////////////////////

/** @type {FilterConsole} */
       const filterConsole = (baseConsole, filter, _topic = undefined) => {
  // TODO do something with optional topic string
  const methodPermits = arrayFilter(
    consoleMethodPermits,
    ([name, _]) => name in baseConsole,
  );
  const methods = arrayMap(methodPermits, ([name, severity]) => {
    /**
     * @param {...any} args
     */
    const method = defineName(name, (...args) => {
      // eslint-disable-next-line @endo/no-polymorphic-call
      if (severity === undefined || filter.canLog(severity)) {
        // @ts-ignore
        // eslint-disable-next-line @endo/no-polymorphic-call
        baseConsole[name](...args);
      }
    });
    return [name, freeze(method)];
  });
  const filteringConsole = fromEntries(methods);
  return /** @type {VirtualConsole} */ (freeze(filteringConsole));
};$h͏_once.filterConsole(filterConsole);
freeze(filterConsole);
})()
,
// === 41. ses ./src/error/unhandled-rejection.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FinalizationRegistry,Map,mapGet,mapDelete,WeakMap,mapSet,finalizationRegistryRegister,weakmapSet,weakmapGet,mapEntries,mapHas;$h͏_imports([["../commons.js", [["FinalizationRegistry",[$h͏_a => (FinalizationRegistry = $h͏_a)]],["Map",[$h͏_a => (Map = $h͏_a)]],["mapGet",[$h͏_a => (mapGet = $h͏_a)]],["mapDelete",[$h͏_a => (mapDelete = $h͏_a)]],["WeakMap",[$h͏_a => (WeakMap = $h͏_a)]],["mapSet",[$h͏_a => (mapSet = $h͏_a)]],["finalizationRegistryRegister",[$h͏_a => (finalizationRegistryRegister = $h͏_a)]],["weakmapSet",[$h͏_a => (weakmapSet = $h͏_a)]],["weakmapGet",[$h͏_a => (weakmapGet = $h͏_a)]],["mapEntries",[$h͏_a => (mapEntries = $h͏_a)]],["mapHas",[$h͏_a => (mapHas = $h͏_a)]]]]]);














/**
 * Create rejection-tracking machinery compatible with Node.js and browsers.
 *
 * Note that modern browsers *prevent* access to the 'unhandledrejection' and
 * 'rejectionhandled' events needed:
 * - in cross-origin mode, like when served from file://
 * - in the browser console (interactively typed-in code)
 * - in the debugger
 *
 * Then, they just look like: `Uncaught (in promise) Error: ...` and don't
 * implement the machinery.
 *
 * The solution is to serve your web page from an http:// or https:// web server
 * and execute actual code.
 *
 * @param {(reason: unknown) => void} reportReason report the reason for an
 * unhandled rejection.
 */
       const makeRejectionHandlers = reportReason => {
  if (FinalizationRegistry === undefined) {
    return undefined;
  }

  /** @typedef {number} ReasonId */
  let lastReasonId = 0;

  /** @type {Map<ReasonId, unknown>} */
  const idToReason = new Map();

  /** @type {(() => void) | undefined} */
  let cancelChecking;

  const removeReasonId = reasonId => {
    mapDelete(idToReason, reasonId);
    if (cancelChecking && idToReason.size === 0) {
      // No more unhandled rejections to check, just cancel the check.
      cancelChecking();
      cancelChecking = undefined;
    }
  };

  /** @type {WeakMap<Promise, ReasonId>} */
  const promiseToReasonId = new WeakMap();

  /**
   * Clean up and report the reason for a GCed unhandled rejection.
   *
   * @param {ReasonId} heldReasonId
   */
  const finalizeDroppedPromise = heldReasonId => {
    if (mapHas(idToReason, heldReasonId)) {
      const reason = mapGet(idToReason, heldReasonId);
      removeReasonId(heldReasonId);
      reportReason(reason);
    }
  };

  /** @type {FinalizationRegistry<ReasonId>} */
  const promiseToReason = new FinalizationRegistry(finalizeDroppedPromise);

  /**
   * Track a rejected promise and its corresponding reason if there is no
   * rejection handler synchronously attached.
   *
   * @param {unknown} reason
   * @param {Promise} pr
   */
  const unhandledRejectionHandler = (reason, pr) => {
    lastReasonId += 1;
    const reasonId = lastReasonId;

    // Update bookkeeping.
    mapSet(idToReason, reasonId, reason);
    weakmapSet(promiseToReasonId, pr, reasonId);
    finalizationRegistryRegister(promiseToReason, pr, reasonId, pr);
  };

  /**
   * Deal with the addition of a handler to a previously rejected promise.
   *
   * Just remove it from our list.  Let the FinalizationRegistry or
   * processTermination report any GCed unhandled rejected promises.
   *
   * @param {Promise} pr
   */
  const rejectionHandledHandler = pr => {
    const reasonId = weakmapGet(promiseToReasonId, pr);
    removeReasonId(reasonId);
  };

  /**
   * Report all the unhandled rejections, now that we are abruptly terminating
   * the agent cluster.
   */
  const processTerminationHandler = () => {
    for (const [reasonId, reason] of mapEntries(idToReason)) {
      removeReasonId(reasonId);
      reportReason(reason);
    }
  };

  return {
    rejectionHandledHandler,
    unhandledRejectionHandler,
    processTerminationHandler,
  };
};$h͏_once.makeRejectionHandlers(makeRejectionHandlers);
})()
,
// === 42. ses ./src/error/tame-console.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let TypeError,apply,defineProperty,freeze,globalThis,defaultHandler,makeCausalConsole,makeRejectionHandlers;$h͏_imports([["../commons.js", [["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["apply",[$h͏_a => (apply = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]]]],["./assert.js", [["loggedErrorHandler",[$h͏_a => (defaultHandler = $h͏_a)]]]],["./console.js", [["makeCausalConsole",[$h͏_a => (makeCausalConsole = $h͏_a)]]]],["./unhandled-rejection.js", [["makeRejectionHandlers",[$h͏_a => (makeRejectionHandlers = $h͏_a)]]]]]);













/**
 * @import {VirtualConsole} from './types.js'
 * @import {GetStackString} from './internal-types.js';
 */

const failFast = message => {
  throw TypeError(message);
};

const wrapLogger = (logger, thisArg) =>
  freeze((...args) => apply(logger, thisArg, args));

/**
 * Wrap console unless suppressed.
 * At the moment, the console is considered a host power in the start
 * compartment, and not a primordial. Hence it is absent from the whilelist
 * and bypasses the intrinsicsCollector.
 *
 * @param {"safe" | "unsafe"} consoleTaming
 * @param {"platform" | "exit" | "abort" | "report" | "none"} [errorTrapping]
 * @param {"report" | "none"} [unhandledRejectionTrapping]
 * @param {GetStackString=} optGetStackString
 */
       const tameConsole = (
  consoleTaming = 'safe',
  errorTrapping = 'platform',
  unhandledRejectionTrapping = 'report',
  optGetStackString = undefined,
) => {
  let loggedErrorHandler;
  if (optGetStackString === undefined) {
    loggedErrorHandler = defaultHandler;
  } else {
    loggedErrorHandler = {
      ...defaultHandler,
      getStackString: optGetStackString,
    };
  }

  // eslint-disable-next-line no-restricted-globals
  const originalConsole = /** @type {VirtualConsole} */ (
    // eslint-disable-next-line no-nested-ternary
    typeof globalThis.console !== 'undefined'
      ? globalThis.console
      : typeof globalThis.print === 'function'
        ? // Make a good-enough console for eshost (including only functions that
          // log at a specific level with no special argument interpretation).
          // https://console.spec.whatwg.org/#logging
          (p => freeze({ debug: p, log: p, info: p, warn: p, error: p }))(
            // eslint-disable-next-line no-undef
            wrapLogger(globalThis.print),
          )
        : undefined
  );

  // Upgrade a log-only console (as in `eshost -h SpiderMonkey`).
  if (originalConsole && originalConsole.log) {
    for (const methodName of ['warn', 'error']) {
      if (!originalConsole[methodName]) {
        defineProperty(originalConsole, methodName, {
          value: wrapLogger(originalConsole.log, originalConsole),
        });
      }
    }
  }

  const ourConsole = /** @type {VirtualConsole} */ (
    consoleTaming === 'unsafe'
      ? originalConsole
      : makeCausalConsole(originalConsole, loggedErrorHandler)
  );

  // Attach platform-specific error traps such that any error that gets thrown
  // at top-of-turn (the bottom of stack) will get logged by our causal
  // console, revealing the diagnostic information associated with the error,
  // including the stack from when the error was created.

  // In the following Node.js and web browser cases, `process` and `window` are
  // spelled as `globalThis` properties to avoid the overweaning gaze of
  // Parcel, which dutifully installs an unnecessary `process` shim if we ever
  // utter that. That unnecessary shim forces the whole bundle into sloppy mode,
  // which in turn breaks SES's strict mode invariant.

  // Disable the polymorphic check for the rest of this file.  It's too noisy
  // when dealing with platform APIs.
  /* eslint-disable @endo/no-polymorphic-call */

  // Node.js
  const globalProcess = globalThis.process || undefined;
  if (
    errorTrapping !== 'none' &&
    typeof globalProcess === 'object' &&
    typeof globalProcess.on === 'function'
  ) {
    let terminate;
    if (errorTrapping === 'platform' || errorTrapping === 'exit') {
      const { exit } = globalProcess;
      // If there is a function-valued process.on but no function-valued process.exit,
      // fail early without caring whether errorTrapping is "platform" only by default.
      typeof exit === 'function' || failFast('missing process.exit');
      terminate = () => exit(globalProcess.exitCode || -1);
    } else if (errorTrapping === 'abort') {
      terminate = globalProcess.abort;
      typeof terminate === 'function' || failFast('missing process.abort');
    }

    globalProcess.on('uncaughtException', error => {
      // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_UNCAUGHT_EXCEPTION.md
      ourConsole.error('SES_UNCAUGHT_EXCEPTION:', error);
      if (terminate) {
        terminate();
      }
    });
  }
  if (
    unhandledRejectionTrapping !== 'none' &&
    typeof globalProcess === 'object' &&
    typeof globalProcess.on === 'function'
  ) {
    const handleRejection = reason => {
      // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_UNHANDLED_REJECTION.md
      ourConsole.error('SES_UNHANDLED_REJECTION:', reason);
      // 'platform' and 'report' just log the reason.
    };
    // Maybe track unhandled promise rejections.
    const h = makeRejectionHandlers(handleRejection);
    if (h) {
      // Rejection handlers are supported.
      globalProcess.on('unhandledRejection', h.unhandledRejectionHandler);
      globalProcess.on('rejectionHandled', h.rejectionHandledHandler);
      globalProcess.on('exit', h.processTerminationHandler);
    }
  }

  // Browser
  const globalWindow = globalThis.window || undefined;
  if (
    errorTrapping !== 'none' &&
    typeof globalWindow === 'object' &&
    typeof globalWindow.addEventListener === 'function'
  ) {
    globalWindow.addEventListener('error', event => {
      event.preventDefault();
      // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_UNCAUGHT_EXCEPTION.md
      ourConsole.error('SES_UNCAUGHT_EXCEPTION:', event.error);
      // 'platform' and 'report' just log the reason.
      if (errorTrapping === 'exit' || errorTrapping === 'abort') {
        globalWindow.location.href = `about:blank`;
      }
    });
  }
  if (
    unhandledRejectionTrapping !== 'none' &&
    typeof globalWindow === 'object' &&
    typeof globalWindow.addEventListener === 'function'
  ) {
    const handleRejection = reason => {
      // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_UNHANDLED_REJECTION.md
      ourConsole.error('SES_UNHANDLED_REJECTION:', reason);
    };

    const h = makeRejectionHandlers(handleRejection);
    if (h) {
      // Rejection handlers are supported.
      globalWindow.addEventListener('unhandledrejection', event => {
        event.preventDefault();
        h.unhandledRejectionHandler(event.reason, event.promise);
      });

      globalWindow.addEventListener('rejectionhandled', event => {
        event.preventDefault();
        h.rejectionHandledHandler(event.promise);
      });

      globalWindow.addEventListener('beforeunload', _event => {
        h.processTerminationHandler();
      });
    }
  }
  /* eslint-enable @endo/no-polymorphic-call */

  return { console: ourConsole };
};$h͏_once.tameConsole(tameConsole);
})()
,
// === 43. ses ./src/error/tame-v8-error-constructor.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let WeakMap,WeakSet,apply,arrayFilter,arrayJoin,arrayMap,arraySlice,create,defineProperties,fromEntries,reflectSet,regexpExec,weakmapGet,weakmapSet,weaksetAdd,weaksetHas,TypeError;$h͏_imports([["../commons.js", [["WeakMap",[$h͏_a => (WeakMap = $h͏_a)]],["WeakSet",[$h͏_a => (WeakSet = $h͏_a)]],["apply",[$h͏_a => (apply = $h͏_a)]],["arrayFilter",[$h͏_a => (arrayFilter = $h͏_a)]],["arrayJoin",[$h͏_a => (arrayJoin = $h͏_a)]],["arrayMap",[$h͏_a => (arrayMap = $h͏_a)]],["arraySlice",[$h͏_a => (arraySlice = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["fromEntries",[$h͏_a => (fromEntries = $h͏_a)]],["reflectSet",[$h͏_a => (reflectSet = $h͏_a)]],["regexpExec",[$h͏_a => (regexpExec = $h͏_a)]],["weakmapGet",[$h͏_a => (weakmapGet = $h͏_a)]],["weakmapSet",[$h͏_a => (weakmapSet = $h͏_a)]],["weaksetAdd",[$h͏_a => (weaksetAdd = $h͏_a)]],["weaksetHas",[$h͏_a => (weaksetHas = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]]]]]);



















// Permit names from https://v8.dev/docs/stack-trace-api
// Permiting only the names used by error-stack-shim/src/v8StackFrames
// callSiteToFrame to shim the error stack proposal.
const safeV8CallSiteMethodNames = [
  // suppress 'getThis' definitely
  'getTypeName',
  // suppress 'getFunction' definitely
  'getFunctionName',
  'getMethodName',
  'getFileName',
  'getLineNumber',
  'getColumnNumber',
  'getEvalOrigin',
  'isToplevel',
  'isEval',
  'isNative',
  'isConstructor',
  'isAsync',
  // suppress 'isPromiseAll' for now
  // suppress 'getPromiseIndex' for now

  // Additional names found by experiment, absent from
  // https://v8.dev/docs/stack-trace-api
  'getPosition',
  'getScriptNameOrSourceURL',

  'toString'  // TODO replace to use only permitted info
];

// TODO this is a ridiculously expensive way to attenuate callsites.
// Before that matters, we should switch to a reasonable representation.
const safeV8CallSiteFacet = callSite => {
  const methodEntry = name => {
    const method = callSite[name];
    return [name, () => apply(method, callSite, [])];
  };
  const o = fromEntries(arrayMap(safeV8CallSiteMethodNames, methodEntry));
  return create(o, {});
};

const safeV8SST = sst => arrayMap(sst, safeV8CallSiteFacet);

// If it has `/node_modules/` anywhere in it, on Node it is likely
// to be a dependent package of the current package, and so to
// be an infrastructure frame to be dropped from concise stack traces.
const FILENAME_NODE_DEPENDENTS_CENSOR = /\/node_modules\//;

// If it begins with `internal/` or `node:internal` then it is likely
// part of the node infrustructre itself, to be dropped from concise
// stack traces.
const FILENAME_NODE_INTERNALS_CENSOR = /^(?:node:)?internal\//;

// Frames within SES `assert.js` should be dropped from concise stack traces, as
// these are just steps towards creating the error object in question.
const FILENAME_ASSERT_CENSOR = /\/packages\/ses\/src\/error\/assert\.js$/;

// Frames within the `eventual-send` shim should be dropped so that concise
// deep stacks omit the internals of the eventual-sending mechanism causing
// asynchronous messages to be sent.
// Note that the eventual-send package will move from agoric-sdk to
// Endo, so this rule will be of general interest.
const FILENAME_EVENTUAL_SEND_CENSOR = /\/packages\/eventual-send\/src\//;

// Frames within the `ses-ava` package should be dropped from concise stack
// traces, as they just support exposing error details to AVA.
const FILENAME_SES_AVA_CENSOR = /\/packages\/ses-ava\/src\/ses-ava-test\.js$/;

// Any stack frame whose `fileName` matches any of these censor patterns
// will be omitted from concise stacks.
// TODO Enable users to configure FILENAME_CENSORS via `lockdown` options.
const FILENAME_CENSORS = [
  FILENAME_NODE_DEPENDENTS_CENSOR,
  FILENAME_NODE_INTERNALS_CENSOR,
  FILENAME_ASSERT_CENSOR,
  FILENAME_EVENTUAL_SEND_CENSOR,
  FILENAME_SES_AVA_CENSOR,
];

// Should a stack frame with this as its fileName be included in a concise
// stack trace?
// Exported only so it can be unit tested.
// TODO Move so that it applies not just to v8.
       const filterFileName = fileName => {
  if (fileName === null) {
    // Seems to suppress builtins like `Array.every (<anonymous>)`
    return false;
  }
  for (const filter of FILENAME_CENSORS) {
    if (regexpExec(filter, fileName)) {
      return false;
    }
  }
  return true;
};

// The ad-hoc rule of the current pattern is that any likely-file-path or
// likely url-path prefix, ending in a `/.../` should get dropped.
// Anything to the left of the likely path text is kept.
// Everything to the right of `/.../` is kept. Thus
// `'Object.bar (/vat-v1/.../errors/test/deep-send.test.js:13:21)'`
// simplifies to
// `'Object.bar (errors/test/deep-send.test.js:13:21)'`.
//
// See thread starting at
// https://github.com/Agoric/agoric-sdk/issues/2326#issuecomment-773020389
$h͏_once.filterFileName(filterFileName);const CALLSITE_ELLIPSIS_PATTERN1=/^((?:.*[( ])?)[:/\w_-]*\/\.\.\.\/(.+)$/;

// The ad-hoc rule of the current pattern is that any likely-file-path or
// likely url-path prefix consisting of `.../` should get dropped.
// Anything to the left of the likely path text is kept.
// Everything to the right of `.../` is kept. Thus
// `'Object.bar (.../errors/test/deep-send.test.js:13:21)'`
// simplifies to
// `'Object.bar (errors/test/deep-send.test.js:13:21)'`.
//
// See thread starting at
// https://github.com/Agoric/agoric-sdk/issues/2326#issuecomment-773020389
const CALLSITE_ELLIPSIS_PATTERN2 = /^((?:.*[( ])?)\.\.\.\/(.+)$/;

// The ad-hoc rule of the current pattern is that any likely-file-path or
// likely url-path prefix, ending in a `/` and prior to `package/` should get
// dropped.
// Anything to the left of the likely path prefix text is kept. `package/` and
// everything to its right is kept. Thus
// `'Object.bar (/Users/markmiller/src/ongithub/agoric/agoric-sdk/packages/errors/test/deep-send.test.js:13:21)'`
// simplifies to
// `'Object.bar (packages/errors/test/deep-send.test.js:13:21)'`.
// Note that `/packages/` is a convention for monorepos encouraged by
// lerna.
const CALLSITE_PACKAGES_PATTERN = /^((?:.*[( ])?)[:/\w_-]*\/(packages\/.+)$/;

// The ad-hoc rule of the current pattern is that any likely-file-path or
// likely url-path prefix of the form `file://` but not `file:///` gets
// dropped.
// Anything to the left of the likely path prefix text is kept. Everything to
// the right of `file://` is kept. Thus
// `'Object.bar (file:///Users/markmiller/src/ongithub/endojs/endo/packages/errors/test/deep-send.test.js:13:21)'` is unchanged but
// `'Object.bar (file://test/deep-send.test.js:13:21)'`

// simplifies to
// `'Object.bar (test/deep-send.test.js:13:21)'`.
// The reason is that `file:///` usually precedes an absolute path which is
// clickable without removing the `file:///`, whereas `file://` usually precedes
// a relative path which, for whatever vscode reason, is not clickable until the
// `file://` is removed.
const CALLSITE_FILE_2SLASH_PATTERN = /^((?:.*[( ])?)file:\/\/([^/].*)$/;

// The use of these callSite patterns below assumes that any match will bind
// capture groups containing the parts of the original string we want
// to keep. The parts outside those capture groups will be dropped from concise
// stacks.
// TODO Enable users to configure CALLSITE_PATTERNS via `lockdown` options.
const CALLSITE_PATTERNS = [
  CALLSITE_ELLIPSIS_PATTERN1,
  CALLSITE_ELLIPSIS_PATTERN2,
  CALLSITE_PACKAGES_PATTERN,
  CALLSITE_FILE_2SLASH_PATTERN,
];

// For a stack frame that should be included in a concise stack trace, if
// `callSiteString` is the original stringified stack frame, return the
// possibly-shorter stringified stack frame that should be shown instead.
// Exported only so it can be unit tested.
// TODO Move so that it applies not just to v8.
/**
 * @param {string} callSiteString
 */
       const shortenCallSiteString = callSiteString => {
  for (const filter of CALLSITE_PATTERNS) {
    const match = regexpExec(filter, callSiteString);
    if (match) {
      return arrayJoin(arraySlice(match, 1), '');
    }
  }
  return callSiteString;
};$h͏_once.shortenCallSiteString(shortenCallSiteString);

       const tameV8ErrorConstructor = (
  OriginalError,
  InitialError,
  errorTaming,
  stackFiltering,
) => {
  if (errorTaming === 'unsafe-debug') {
    throw TypeError(
      'internal: v8+unsafe-debug special case should already be done',
    );
  }
  // TODO: Proper CallSite types
  /** @typedef {{}} CallSite */

  const originalCaptureStackTrace = OriginalError.captureStackTrace;

  const omitFrames =
    stackFiltering === 'concise' || stackFiltering === 'omit-frames';

  const shortenPaths =
    stackFiltering === 'concise' || stackFiltering === 'shorten-paths';

  // const callSiteFilter = _callSite => true;
  const callSiteFilter = callSite => {
    if (omitFrames) {
      // eslint-disable-next-line @endo/no-polymorphic-call
      if (callSite.getFunctionName()?.startsWith('__HIDE_')) {
        return false;
      }
      // eslint-disable-next-line @endo/no-polymorphic-call
      return filterFileName(callSite.getFileName());
    }
    return true;
  };

  const callSiteStringifier = callSite => {
    let callSiteString = `${callSite}`;
    if (shortenPaths) {
      callSiteString = shortenCallSiteString(callSiteString);
    }
    return `\n  at ${callSiteString}`;
  };

  const stackStringFromSST = (_error, sst) =>
    arrayJoin(
      arrayMap(arrayFilter(sst, callSiteFilter), callSiteStringifier),
      '',
    );

  /**
   * @typedef {object} StructuredStackInfo
   * @property {CallSite[]} callSites
   * @property {undefined} [stackString]
   */

  /**
   * @typedef {object} ParsedStackInfo
   * @property {undefined} [callSites]
   * @property {string} stackString
   */

  // Mapping from error instance to the stack for that instance.
  // The stack info is either the structured stack trace
  // or the generated tamed stack string
  /** @type {WeakMap<Error, ParsedStackInfo | StructuredStackInfo>} */
  const stackInfos = new WeakMap();

  // Use concise methods to obtain named functions without constructors.
  const tamedMethods = {
    // The optional `optFn` argument is for cutting off the bottom of
    // the stack --- for capturing the stack only above the topmost
    // call to that function. Since this isn't the "real" captureStackTrace
    // but instead calls the real one, if no other cutoff is provided,
    // we cut this one off.
    captureStackTrace(error, optFn = tamedMethods.captureStackTrace) {
      if (typeof originalCaptureStackTrace === 'function') {
        // OriginalError.captureStackTrace is only on v8
        apply(originalCaptureStackTrace, OriginalError, [error, optFn]);
        return;
      }
      reflectSet(error, 'stack', '');
    },
    // Shim of proposed special power, to reside by default only
    // in the start compartment, for getting the stack traceback
    // string associated with an error.
    // See https://tc39.es/proposal-error-stacks/
    getStackString(error) {
      let stackInfo = weakmapGet(stackInfos, error);

      if (stackInfo === undefined) {
        // The following will call `prepareStackTrace()` synchronously
        // which will populate stackInfos
        // eslint-disable-next-line no-void
        void error.stack;
        stackInfo = weakmapGet(stackInfos, error);
        if (!stackInfo) {
          stackInfo = { stackString: '' };
          weakmapSet(stackInfos, error, stackInfo);
        }
      }

      // prepareStackTrace() may generate the stackString
      // if errorTaming === 'unsafe'

      if (stackInfo.stackString !== undefined) {
        return stackInfo.stackString;
      }

      const stackString = stackStringFromSST(error, stackInfo.callSites);
      weakmapSet(stackInfos, error, { stackString });

      return stackString;
    },
    prepareStackTrace(error, sst) {
      if (errorTaming === 'unsafe') {
        const stackString = stackStringFromSST(error, sst);
        weakmapSet(stackInfos, error, { stackString });
        return `${error}${stackString}`;
      } else {
        weakmapSet(stackInfos, error, { callSites: sst });
        return '';
      }
    },
  };

  // A prepareFn is a prepareStackTrace function.
  // An sst is a `structuredStackTrace`, which is an array of
  // callsites.
  // A user prepareFn is a prepareFn defined by a client of this API,
  // and provided by assigning to `Error.prepareStackTrace`.
  // A user prepareFn should only receive an attenuated sst, which
  // is an array of attenuated callsites.
  // A system prepareFn is the prepareFn created by this module to
  // be installed on the real `Error` constructor, to receive
  // an original sst, i.e., an array of unattenuated callsites.
  // An input prepareFn is a function the user assigns to
  // `Error.prepareStackTrace`, which might be a user prepareFn or
  // a system prepareFn previously obtained by reading
  // `Error.prepareStackTrace`.

  const defaultPrepareFn = tamedMethods.prepareStackTrace;

  OriginalError.prepareStackTrace = defaultPrepareFn;

  // A weakset branding some functions as system prepareFns, all of which
  // must be defined by this module, since they can receive an
  // unattenuated sst.
  const systemPrepareFnSet = new WeakSet([defaultPrepareFn]);

  const systemPrepareFnFor = inputPrepareFn => {
    if (weaksetHas(systemPrepareFnSet, inputPrepareFn)) {
      return inputPrepareFn;
    }
    // Use concise methods to obtain named functions without constructors.
    const systemMethods = {
      prepareStackTrace(error, sst) {
        weakmapSet(stackInfos, error, { callSites: sst });
        return inputPrepareFn(error, safeV8SST(sst));
      },
    };
    weaksetAdd(systemPrepareFnSet, systemMethods.prepareStackTrace);
    return systemMethods.prepareStackTrace;
  };

  // Note `stackTraceLimit` accessor already defined by
  // tame-error-constructor.js
  defineProperties(InitialError, {
    captureStackTrace: {
      value: tamedMethods.captureStackTrace,
      writable: true,
      enumerable: false,
      configurable: true,
    },
    prepareStackTrace: {
      get() {
        return OriginalError.prepareStackTrace;
      },
      set(inputPrepareStackTraceFn) {
        if (typeof inputPrepareStackTraceFn === 'function') {
          const systemPrepareFn = systemPrepareFnFor(inputPrepareStackTraceFn);
          OriginalError.prepareStackTrace = systemPrepareFn;
        } else {
          OriginalError.prepareStackTrace = defaultPrepareFn;
        }
      },
      enumerable: false,
      configurable: true,
    },
  });

  return tamedMethods.getStackString;
};$h͏_once.tameV8ErrorConstructor(tameV8ErrorConstructor);
})()
,
// === 44. ses ./src/error/tame-error-constructor.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_ERROR,apply,construct,defineProperties,setPrototypeOf,getOwnPropertyDescriptor,defineProperty,getOwnPropertyDescriptors,NativeErrors,tameV8ErrorConstructor;$h͏_imports([["../commons.js", [["FERAL_ERROR",[$h͏_a => (FERAL_ERROR = $h͏_a)]],["apply",[$h͏_a => (apply = $h͏_a)]],["construct",[$h͏_a => (construct = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["setPrototypeOf",[$h͏_a => (setPrototypeOf = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]]]],["../permits.js", [["NativeErrors",[$h͏_a => (NativeErrors = $h͏_a)]]]],["./tame-v8-error-constructor.js", [["tameV8ErrorConstructor",[$h͏_a => (tameV8ErrorConstructor = $h͏_a)]]]]]);












// Present on at least FF and XS. Proposed by Error-proposal. The original
// is dangerous, so tameErrorConstructor replaces it with a safe one.
// We grab the original here before it gets replaced.
const stackDesc = getOwnPropertyDescriptor(FERAL_ERROR.prototype, 'stack');
const stackGetter = stackDesc && stackDesc.get;

// Use concise methods to obtain named functions without constructors.
const tamedMethods = {
  getStackString(error) {
    if (typeof stackGetter === 'function') {
      return apply(stackGetter, error, []);
    } else if ('stack' in error) {
      // The fallback is to just use the de facto `error.stack` if present
      return `${error.stack}`;
    }
    return '';
  },
};
let initialGetStackString = tamedMethods.getStackString;

               function tameErrorConstructor(
  errorTaming = 'safe',
  stackFiltering = 'concise',
) {
  const ErrorPrototype = FERAL_ERROR.prototype;

  const { captureStackTrace: originalCaptureStackTrace } = FERAL_ERROR;
  const platform =
    typeof originalCaptureStackTrace === 'function' ? 'v8' : 'unknown';

  const makeErrorConstructor = (_ = {}) => {
    // eslint-disable-next-line no-shadow
    const ResultError = function Error(...rest) {
      let error;
      if (new.target === undefined) {
        error = apply(FERAL_ERROR, this, rest);
      } else {
        error = construct(FERAL_ERROR, rest, new.target);
      }
      if (platform === 'v8') {
        // TODO Likely expensive!
        apply(originalCaptureStackTrace, FERAL_ERROR, [error, ResultError]);
      }
      return error;
    };
    defineProperties(ResultError, {
      length: { value: 1 },
      prototype: {
        value: ErrorPrototype,
        writable: false,
        enumerable: false,
        configurable: false,
      },
    });
    return ResultError;
  };
  const InitialError = makeErrorConstructor({ powers: 'original' });
  const SharedError = makeErrorConstructor({ powers: 'none' });
  defineProperties(ErrorPrototype, {
    constructor: { value: SharedError },
  });

  for (const NativeError of NativeErrors) {
    setPrototypeOf(NativeError, SharedError);
  }

  // https://v8.dev/docs/stack-trace-api#compatibility advises that
  // programmers can "always" set `Error.stackTraceLimit`
  // even on non-v8 platforms. On non-v8
  // it will have no effect, but this advice only makes sense
  // if the assignment itself does not fail, which it would
  // if `Error` were naively frozen. Hence, we add setters that
  // accept but ignore the assignment on non-v8 platforms.
  defineProperties(InitialError, {
    stackTraceLimit: {
      get() {
        if (typeof FERAL_ERROR.stackTraceLimit === 'number') {
          // FERAL_ERROR.stackTraceLimit is only on v8
          return FERAL_ERROR.stackTraceLimit;
        }
        return undefined;
      },
      set(newLimit) {
        if (typeof newLimit !== 'number') {
          // silently do nothing. This behavior doesn't precisely
          // emulate v8 edge-case behavior. But given the purpose
          // of this emulation, having edge cases err towards
          // harmless seems the safer option.
          return;
        }
        if (typeof FERAL_ERROR.stackTraceLimit === 'number') {
          // FERAL_ERROR.stackTraceLimit is only on v8
          FERAL_ERROR.stackTraceLimit = newLimit;
          // We place the useless return on the next line to ensure
          // that anything we place after the if in the future only
          // happens if the then-case does not.
          // eslint-disable-next-line no-useless-return
          return;
        }
      },
      // WTF on v8 stackTraceLimit is enumerable
      enumerable: false,
      configurable: true,
    },
  });

  if (errorTaming === 'unsafe-debug' && platform === 'v8') {
    // This case is a kludge to work around
    // https://github.com/endojs/endo/issues/1798
    // https://github.com/endojs/endo/issues/2348
    // https://github.com/Agoric/agoric-sdk/issues/8662

    defineProperties(InitialError, {
      prepareStackTrace: {
        get() {
          return FERAL_ERROR.prepareStackTrace;
        },
        set(newPrepareStackTrace) {
          FERAL_ERROR.prepareStackTrace = newPrepareStackTrace;
        },
        enumerable: false,
        configurable: true,
      },
      captureStackTrace: {
        value: FERAL_ERROR.captureStackTrace,
        writable: true,
        enumerable: false,
        configurable: true,
      },
    });

    const descs = getOwnPropertyDescriptors(InitialError);
    defineProperties(SharedError, {
      stackTraceLimit: descs.stackTraceLimit,
      prepareStackTrace: descs.prepareStackTrace,
      captureStackTrace: descs.captureStackTrace,
    });

    return {
      '%InitialGetStackString%': initialGetStackString,
      '%InitialError%': InitialError,
      '%SharedError%': SharedError,
    };
  }

  // The default SharedError much be completely powerless even on v8,
  // so the lenient `stackTraceLimit` accessor does nothing on all
  // platforms.
  defineProperties(SharedError, {
    stackTraceLimit: {
      get() {
        return undefined;
      },
      set(_newLimit) {
        // do nothing
      },
      enumerable: false,
      configurable: true,
    },
  });

  if (platform === 'v8') {
    // `SharedError.prepareStackTrace`, if it exists, must also be
    // powerless. However, from what we've heard, depd expects to be able to
    // assign to it without the assignment throwing. It is normally a function
    // that returns a stack string to be magically added to error objects.
    // However, as long as we're adding a lenient standin, we may as well
    // accommodate any who expect to get a function they can call and get
    // a string back. This prepareStackTrace is a do-nothing function that
    // always returns the empty string.
    defineProperties(SharedError, {
      prepareStackTrace: {
        get() {
          return () => '';
        },
        set(_prepareFn) {
          // do nothing
        },
        enumerable: false,
        configurable: true,
      },
      captureStackTrace: {
        value: (errorish, _constructorOpt) => {
          defineProperty(errorish, 'stack', {
            value: '',
          });
        },
        writable: false,
        enumerable: false,
        configurable: true,
      },
    });
  }

  if (platform === 'v8') {
    initialGetStackString = tameV8ErrorConstructor(
      FERAL_ERROR,
      InitialError,
      errorTaming,
      stackFiltering,
    );
  } else if (errorTaming === 'unsafe' || errorTaming === 'unsafe-debug') {
    // v8 has too much magic around their 'stack' own property for it to
    // coexist cleanly with this accessor. So only install it on non-v8

    // Error.prototype.stack property as proposed at
    // https://tc39.es/proposal-error-stacks/
    // with the fix proposed at
    // https://github.com/tc39/proposal-error-stacks/issues/46
    // On others, this still protects from the override mistake,
    // essentially like enable-property-overrides.js would
    // once this accessor property itself is frozen, as will happen
    // later during lockdown.
    //
    // However, there is here a change from the intent in the current
    // state of the proposal. If experience tells us whether this change
    // is a good idea, we should modify the proposal accordingly. There is
    // much code in the world that assumes `error.stack` is a string. So
    // where the proposal accommodates secure operation by making the
    // property optional, we instead accommodate secure operation by
    // having the secure form always return only the stable part, the
    // stringified error instance, and omitting all the frame information
    // rather than omitting the property.
    defineProperties(ErrorPrototype, {
      stack: {
        get() {
          return initialGetStackString(this);
        },
        set(newValue) {
          defineProperties(this, {
            stack: {
              value: newValue,
              writable: true,
              enumerable: true,
              configurable: true,
            },
          });
        },
      },
    });
  } else {
    // v8 has too much magic around their 'stack' own property for it to
    // coexist cleanly with this accessor. So only install it on non-v8
    defineProperties(ErrorPrototype, {
      stack: {
        get() {
          // https://github.com/tc39/proposal-error-stacks/issues/46
          // allows this to not add an unpleasant newline. Otherwise
          // we should fix this.
          return `${this}`;
        },
        set(newValue) {
          defineProperties(this, {
            stack: {
              value: newValue,
              writable: true,
              enumerable: true,
              configurable: true,
            },
          });
        },
      },
    });
  }

  return {
    '%InitialGetStackString%': initialGetStackString,
    '%InitialError%': InitialError,
    '%SharedError%': SharedError,
  };
}$h͏_once.default(      tameErrorConstructor);
})()
,
// === 45. ses ./src/module-load.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let getenv,Map,Set,TypeError,arrayJoin,arrayMap,arrayPush,arraySome,create,freeze,generatorNext,generatorThrow,getOwnPropertyNames,isArray,isPrimitive,mapGet,mapHas,mapSet,promiseThen,setAdd,values,weakmapGet,weakmapHas,makeError,annotateError,q,b,X;$h͏_imports([["@endo/env-options", [["getEnvironmentOption",[$h͏_a => (getenv = $h͏_a)]]]],["./commons.js", [["Map",[$h͏_a => (Map = $h͏_a)]],["Set",[$h͏_a => (Set = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["arrayJoin",[$h͏_a => (arrayJoin = $h͏_a)]],["arrayMap",[$h͏_a => (arrayMap = $h͏_a)]],["arrayPush",[$h͏_a => (arrayPush = $h͏_a)]],["arraySome",[$h͏_a => (arraySome = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["generatorNext",[$h͏_a => (generatorNext = $h͏_a)]],["generatorThrow",[$h͏_a => (generatorThrow = $h͏_a)]],["getOwnPropertyNames",[$h͏_a => (getOwnPropertyNames = $h͏_a)]],["isArray",[$h͏_a => (isArray = $h͏_a)]],["isPrimitive",[$h͏_a => (isPrimitive = $h͏_a)]],["mapGet",[$h͏_a => (mapGet = $h͏_a)]],["mapHas",[$h͏_a => (mapHas = $h͏_a)]],["mapSet",[$h͏_a => (mapSet = $h͏_a)]],["promiseThen",[$h͏_a => (promiseThen = $h͏_a)]],["setAdd",[$h͏_a => (setAdd = $h͏_a)]],["values",[$h͏_a => (values = $h͏_a)]],["weakmapGet",[$h͏_a => (weakmapGet = $h͏_a)]],["weakmapHas",[$h͏_a => (weakmapHas = $h͏_a)]]]],["./error/assert.js", [["makeError",[$h͏_a => (makeError = $h͏_a)]],["annotateError",[$h͏_a => (annotateError = $h͏_a)]],["q",[$h͏_a => (q = $h͏_a)]],["b",[$h͏_a => (b = $h͏_a)]],["X",[$h͏_a => (X = $h͏_a)]]]]]);


























const noop = () => {};

const asyncTrampoline = async (generatorFunc, args, errorWrapper) => {
  await null;
  const iterator = generatorFunc(...args);
  let result = generatorNext(iterator);
  while (!result.done) {
    try {
      // eslint-disable-next-line no-await-in-loop
      const val = await result.value;
      result = generatorNext(iterator, val);
    } catch (error) {
      result = generatorThrow(iterator, errorWrapper(error));
    }
  }
  return result.value;
};

const syncTrampoline = (generatorFunc, args) => {
  const iterator = generatorFunc(...args);
  let result = generatorNext(iterator);
  while (!result.done) {
    try {
      result = generatorNext(iterator, result.value);
    } catch (error) {
      result = generatorThrow(iterator, error);
    }
  }
  return result.value;
};

// `makeAlias` constructs compartment specifier tuples for the `aliases`
// private field of compartments.
// These aliases allow a compartment to alias an internal module specifier to a
// module specifier in an external compartment, and also to create internal
// aliases.
// Both are facilitated by the moduleMap Compartment constructor option.
       const makeAlias = (compartment, specifier) =>
  freeze({ compartment, specifier });

// `resolveAll` pre-computes resolutions of all imports within the compartment
// in which a module was loaded.
$h͏_once.makeAlias(makeAlias);const resolveAll=(imports,resolveHook,fullReferrerSpecifier)=>{
  const resolvedImports = create(null);
  for (const importSpecifier of imports) {
    const fullSpecifier = resolveHook(importSpecifier, fullReferrerSpecifier);
    resolvedImports[importSpecifier] = fullSpecifier;
  }
  return freeze(resolvedImports);
};

const loadModuleSource = (
  compartmentPrivateFields,
  moduleAliases,
  compartment,
  moduleSpecifier,
  moduleSource,
  enqueueJob,
  selectImplementation,
  moduleLoads,
  importMeta,
) => {
  const { resolveHook, name: compartmentName } = weakmapGet(
    compartmentPrivateFields,
    compartment,
  );

  const { imports } = moduleSource;
  if (
    !isArray(imports) ||
    arraySome(imports, specifier => typeof specifier !== 'string')
  ) {
    throw makeError(
      X`Invalid module source: 'imports' must be an array of strings, got ${imports} for module ${q(moduleSpecifier)} of compartment ${q(compartmentName)}`,
    );
  }

  // resolve all imports relative to this referrer module.
  const resolvedImports = resolveAll(imports, resolveHook, moduleSpecifier);
  const moduleRecord = freeze({
    compartment,
    moduleSource,
    moduleSpecifier,
    resolvedImports,
    importMeta,
  });

  // Enqueue jobs to load this module's shallow dependencies.
  for (const fullSpecifier of values(resolvedImports)) {
    // Behold: recursion.
    // eslint-disable-next-line no-use-before-define
    enqueueJob(memoizedLoadWithErrorAnnotation, [
      compartmentPrivateFields,
      moduleAliases,
      compartment,
      fullSpecifier,
      enqueueJob,
      selectImplementation,
      moduleLoads,
    ]);
  }

  return moduleRecord;
};

function* loadWithoutErrorAnnotation(
  compartmentPrivateFields,
  moduleAliases,
  compartment,
  moduleSpecifier,
  enqueueJob,
  selectImplementation,
  moduleLoads,
) {
  const {
    importHook,
    importNowHook,
    moduleMap,
    moduleMapHook,
    moduleRecords,
    parentCompartment,
  } = weakmapGet(compartmentPrivateFields, compartment);

  if (mapHas(moduleRecords, moduleSpecifier)) {
    return mapGet(moduleRecords, moduleSpecifier);
  }

  // Follow moduleMap, or moduleMapHook if present.
  let moduleDescriptor = moduleMap[moduleSpecifier];
  if (moduleDescriptor === undefined && moduleMapHook !== undefined) {
    moduleDescriptor = moduleMapHook(moduleSpecifier);
  }
  if (moduleDescriptor === undefined) {
    const moduleHook = selectImplementation(importHook, importNowHook);
    if (moduleHook === undefined) {
      const moduleHookName = selectImplementation(
        'importHook',
        'importNowHook',
      );
      throw makeError(
        X`${b(moduleHookName)} needed to load module ${q(
          moduleSpecifier,
        )} in compartment ${q(compartment.name)}`,
      );
    }
    moduleDescriptor = moduleHook(moduleSpecifier);
    // Uninitialized module namespaces throw if we attempt to coerce them into
    // promises.
    if (!weakmapHas(moduleAliases, moduleDescriptor)) {
      moduleDescriptor = yield moduleDescriptor;
    }
  }

  if (typeof moduleDescriptor === 'string') {
    // eslint-disable-next-line @endo/no-polymorphic-call
    throw makeError(
      X`Cannot map module ${q(moduleSpecifier)} to ${q(
        moduleDescriptor,
      )} in parent compartment, use {source} module descriptor`,
      TypeError,
    );
  } else if (!isPrimitive(moduleDescriptor)) {
    // In this shim (and not in XS, and not in the standard we imagine), we
    // allow a module namespace object to stand in for a module descriptor that
    // describes its original {compartment, specifier} so that it can be used
    // to create a link.
    let aliasDescriptor = weakmapGet(moduleAliases, moduleDescriptor);
    if (aliasDescriptor !== undefined) {
      moduleDescriptor = aliasDescriptor;
    }

    if (moduleDescriptor.namespace !== undefined) {
      // { namespace: string, compartment?: Compartment }
      // Namespace module descriptors link to a module instance.

      if (typeof moduleDescriptor.namespace === 'string') {
        // The default compartment is the *parent*, not this child compartment.
        // This is a difference from the legacy {specifier, compartment} module
        // descriptor.
        const {
          compartment: aliasCompartment = parentCompartment,
          namespace: aliasSpecifier,
        } = moduleDescriptor;
        if (
          isPrimitive(aliasCompartment) ||
          !weakmapHas(compartmentPrivateFields, aliasCompartment)
        ) {
          throw makeError(
            X`Invalid compartment in module descriptor for specifier ${q(moduleSpecifier)} in compartment ${q(compartment.name)}`,
          );
        }
        // Behold: recursion.
        // eslint-disable-next-line no-use-before-define
        const aliasRecord = yield memoizedLoadWithErrorAnnotation(
          compartmentPrivateFields,
          moduleAliases,
          aliasCompartment,
          aliasSpecifier,
          enqueueJob,
          selectImplementation,
          moduleLoads,
        );
        mapSet(moduleRecords, moduleSpecifier, aliasRecord);
        return aliasRecord;
      }

      // All remaining objects must either be a module namespace, or be
      // promoted into a module namespace with a virtual module source.
      if (!isPrimitive(moduleDescriptor.namespace)) {
        const { namespace } = moduleDescriptor;
        // Brand-check SES shim module exports namespaces:
        aliasDescriptor = weakmapGet(moduleAliases, namespace);
        if (aliasDescriptor !== undefined) {
          moduleDescriptor = aliasDescriptor;
          // Fall through to processing the resulting {compartment, specifier}
          // alias.
        } else {
          // Promote an arbitrary object to a module namespace with a virtual
          // module source.
          // { namespace: Object }
          const exports = getOwnPropertyNames(namespace);
          /** @type {import('../types.js').VirtualModuleSource} */
          const moduleSource = {
            imports: [],
            exports,
            execute(env) {
              for (const name of exports) {
                env[name] = namespace[name];
              }
            },
          };
          const importMeta = undefined;
          const moduleRecord = loadModuleSource(
            compartmentPrivateFields,
            moduleAliases,
            compartment,
            moduleSpecifier,
            moduleSource,
            enqueueJob,
            selectImplementation,
            moduleLoads,
            importMeta,
          );
          mapSet(moduleRecords, moduleSpecifier, moduleRecord);
          return moduleRecord;
        }
      } else {
        throw makeError(
          X`Invalid compartment in module descriptor for specifier ${q(moduleSpecifier)} in compartment ${q(compartment.name)}`,
        );
      }
    }

    if (moduleDescriptor.source !== undefined) {
      // Module source descriptors create an instance from a module source.
      // The descriptor may contain the module source, or refer to a source
      // loaded in a particular compartment.

      if (typeof moduleDescriptor.source === 'string') {
        // { source: string, importMeta?, specifier?: string, compartment? }
        // A string source is the specifier for a different module source.
        // That source may come from this compartment's parent (default), or
        // from a specified compartment, and the specified compartment may be
        // this compartment to make a duplicate.

        const {
          source: loaderSpecifier,
          specifier: instanceSpecifier = moduleSpecifier,
          compartment: loaderCompartment = parentCompartment,
          importMeta = undefined,
        } = moduleDescriptor;

        // Induce the compartment, possibly a different compartment
        // to load a module source.

        // Behold: recursion.
        // eslint-disable-next-line no-use-before-define
        const loaderRecord = yield memoizedLoadWithErrorAnnotation(
          compartmentPrivateFields,
          moduleAliases,
          loaderCompartment,
          loaderSpecifier,
          enqueueJob,
          selectImplementation,
          moduleLoads,
        );

        // Extract the source of the module from the loader compartment's
        // record.
        const { moduleSource } = loaderRecord;

        // Instantiate that source in our own compartment, possibly with a
        // different specifier for resolving its own imports.
        const moduleRecord = loadModuleSource(
          compartmentPrivateFields,
          moduleAliases,
          compartment,
          instanceSpecifier,
          moduleSource,
          enqueueJob,
          selectImplementation,
          moduleLoads,
          importMeta,
        );
        mapSet(moduleRecords, moduleSpecifier, moduleRecord);
        return moduleRecord;
      } else {
        // { source: ModuleSource, importMeta?, specifier?: string }
        // We assume all non-string module sources are any of the supported
        // kinds of module source: PrecompiledModuleSource,
        // VirtualModuleSource, or a native ModuleSource.

        const {
          source: moduleSource,
          specifier: aliasSpecifier = moduleSpecifier,
          importMeta,
        } = moduleDescriptor;

        const aliasRecord = loadModuleSource(
          compartmentPrivateFields,
          moduleAliases,
          compartment,
          aliasSpecifier,
          moduleSource,
          enqueueJob,
          selectImplementation,
          moduleLoads,
          importMeta,
        );
        mapSet(moduleRecords, moduleSpecifier, aliasRecord);
        return aliasRecord;
      }
    }

    if (moduleDescriptor.archive !== undefined) {
      // { archive: Archive, path: string }
      // We do not support this XS-native module descriptor.
      throw makeError(
        X`Unsupported archive module descriptor for specifier ${q(moduleSpecifier)} in compartment ${q(compartment.name)}`,
      );
    }

    // { record, specifier?, compartment?, importMeta? }
    // A (legacy) module descriptor for when we find the module source (record)
    // but at a different specifier than requested.
    // Providing this {specifier, record} descriptor serves as an ergonomic
    // short-hand for stashing the record, returning a {compartment, specifier}
    // reference, bouncing the module hook, then producing the source (record)
    // when module hook receives the response specifier.
    if (moduleDescriptor.record !== undefined) {
      const {
        compartment: aliasCompartment = compartment,
        specifier: aliasSpecifier = moduleSpecifier,
        record: moduleSource,
        importMeta,
      } = moduleDescriptor;

      const aliasRecord = loadModuleSource(
        compartmentPrivateFields,
        moduleAliases,
        aliasCompartment,
        aliasSpecifier,
        moduleSource,
        enqueueJob,
        selectImplementation,
        moduleLoads,
        importMeta,
      );
      mapSet(moduleRecords, moduleSpecifier, aliasRecord);
      mapSet(moduleRecords, aliasSpecifier, aliasRecord);
      return aliasRecord;
    }

    // { specifier: string, compartment: Compartment }
    // A (legacy) module descriptor that describes a link to a module instance
    // in a specified compartment.
    if (
      moduleDescriptor.compartment !== undefined &&
      moduleDescriptor.specifier !== undefined
    ) {
      if (
        isPrimitive(moduleDescriptor.compartment) ||
        !weakmapHas(compartmentPrivateFields, moduleDescriptor.compartment) ||
        typeof moduleDescriptor.specifier !== 'string'
      ) {
        throw makeError(
          X`Invalid compartment in module descriptor for specifier ${q(moduleSpecifier)} in compartment ${q(compartment.name)}`,
        );
      }
      // Behold: recursion.
      // eslint-disable-next-line no-use-before-define
      const aliasRecord = yield memoizedLoadWithErrorAnnotation(
        compartmentPrivateFields,
        moduleAliases,
        moduleDescriptor.compartment,
        moduleDescriptor.specifier,
        enqueueJob,
        selectImplementation,
        moduleLoads,
      );
      mapSet(moduleRecords, moduleSpecifier, aliasRecord);
      return aliasRecord;
    }

    // A (legacy) behavior: If we do not recognize the module descriptor as a
    // module descriptor, we assume that it is a module source (record):
    const moduleSource = moduleDescriptor;
    const moduleRecord = loadModuleSource(
      compartmentPrivateFields,
      moduleAliases,
      compartment,
      moduleSpecifier,
      moduleSource,
      enqueueJob,
      selectImplementation,
      moduleLoads,
    );
    // Memoize.
    mapSet(moduleRecords, moduleSpecifier, moduleRecord);
    return moduleRecord;
  } else {
    throw makeError(
      X`module descriptor must be a string or object for specifier ${q(
        moduleSpecifier,
      )} in compartment ${q(compartment.name)}`,
    );
  }
}

const memoizedLoadWithErrorAnnotation = (
  compartmentPrivateFields,
  moduleAliases,
  compartment,
  moduleSpecifier,
  enqueueJob,
  selectImplementation,
  moduleLoads,
) => {
  const { name: compartmentName } = weakmapGet(
    compartmentPrivateFields,
    compartment,
  );

  // Prevent data-lock from recursion into branches visited in dependent loads.
  let compartmentLoading = mapGet(moduleLoads, compartment);
  if (compartmentLoading === undefined) {
    compartmentLoading = new Map();
    mapSet(moduleLoads, compartment, compartmentLoading);
  }
  let moduleLoading = mapGet(compartmentLoading, moduleSpecifier);
  if (moduleLoading !== undefined) {
    return moduleLoading;
  }

  moduleLoading = selectImplementation(asyncTrampoline, syncTrampoline)(
    loadWithoutErrorAnnotation,
    [
      compartmentPrivateFields,
      moduleAliases,
      compartment,
      moduleSpecifier,
      enqueueJob,
      selectImplementation,
      moduleLoads,
    ],
    error => {
      // eslint-disable-next-line @endo/no-polymorphic-call
      annotateError(
        error,
        X`${error.message}, loading ${q(moduleSpecifier)} in compartment ${q(
          compartmentName,
        )}`,
      );
      throw error;
    },
  );

  mapSet(compartmentLoading, moduleSpecifier, moduleLoading);

  return moduleLoading;
};

/**
 * If `aggregateErrors` is `false`, the `errors` property of the fulfilled object
 * will always be empty.
 * @param {{errors?: Error[], noAggregateErrors?: boolean}} [options]
 */
const asyncJobQueue = ({ errors = [], noAggregateErrors = false } = {}) => {
  /** @type {Set<Promise<undefined>>} */
  const pendingJobs = new Set();

  /**
   * Enqueues a job that starts immediately but won't be awaited until drainQueue is called.
   *
   * @template {(...args: any[]) => Promise<void>} F
   * @param {F} func - An async function to execute
   * @param {Parameters<F>} args - Arguments to pass to the function
   * @returns {void}
   */
  const enqueueJob = (func, args) => {
    setAdd(
      pendingJobs,
      promiseThen(func(...args), noop, error => {
        if (noAggregateErrors) {
          throw error;
        } else {
          arrayPush(errors, error);
        }
      }),
    );
  };
  /**
   * Sequentially awaits pending jobs and returns an array of errors
   */
  const drainQueue = async () => {
    await null;
    for (const job of pendingJobs) {
      // eslint-disable-next-line no-await-in-loop
      await job;
    }
  };
  return { enqueueJob, drainQueue, errors };
};

/**
 * If `aggregateErrors` is `false`, the `errors` property of the returned object
 * will always be empty.
 * @param {{errors?: Error[], noAggregateErrors?: boolean}} [options]
 */
const syncJobQueue = ({ errors = [], noAggregateErrors = false } = {}) => {
  let current = [];
  let next = [];

  /**
   * Enqueues a job
   *
   * @template {(...args: any[]) => void} F
   * @param {F} func - An async function to execute
   * @param {Parameters<F>} args - Arguments to pass to the function
   * @returns {void}
   */
  const enqueueJob = (func, args) => {
    arrayPush(next, [func, args]);
  };
  const drainQueue = () => {
    // Attention: load bearing flow order. Calling another enqueued function in the
    // synchronous usecase must happen after the one that enqueued it has finished.
    // Jobs enqueued in one pass do not interleave with jobs resulting from them.
    // It's necessary for efficient memoization and to break cycles.
    for (const [func, args] of current) {
      try {
        func(...args);
      } catch (error) {
        if (noAggregateErrors) {
          throw error;
        } else {
          arrayPush(errors, error);
        }
      }
    }
    current = next;
    next = [];
    if (current.length > 0) drainQueue();
  };
  return { enqueueJob, drainQueue, errors };
};

/**
 * @param {object} options
 * @param {Array<Error>} options.errors
 * @param {string} options.errorPrefix
 */
const throwAggregateError = ({ errors, errorPrefix }) => {
  // Throw an aggregate error if there were any errors.
  if (errors.length > 0) {
    const verbose =
      /** @type {'' | 'verbose'} */
      (getenv('COMPARTMENT_LOAD_ERRORS', '', ['verbose'])) === 'verbose';
    throw TypeError(
      `${errorPrefix} (${errors.length} underlying failures: ${arrayJoin(
        arrayMap(errors, error => error.message + (verbose ? error.stack : '')),
        ', ',
      )}`,
    );
  }
};

const preferSync = (_asyncImpl, syncImpl) => syncImpl;
const preferAsync = (asyncImpl, _syncImpl) => asyncImpl;

/**
 * `load` asynchronously gathers the module records for a module and its
 * transitive dependencies.
 * The module records refer to each other by a reference to the dependency's
 * compartment and the specifier of the module within its own compartment.
 * This graph is then ready to be synchronously linked and executed.
 * @param {WeakMap<Compartment, any>} compartmentPrivateFields
 * @param {WeakMap<object, object>} moduleAliases
 * @param {Compartment} compartment
 * @param {string} moduleSpecifier - The module specifier to load.
 * @param {{ noAggregateErrors?: boolean}} options
 */
       const load = async (
  compartmentPrivateFields,
  moduleAliases,
  compartment,
  moduleSpecifier,
  { noAggregateErrors = false } = {},
) => {
  const { name: compartmentName } = weakmapGet(
    compartmentPrivateFields,
    compartment,
  );

  /** @type {Map<object, Map<string, Promise<Record<any, any>>>>} */
  const moduleLoads = new Map();

  const { enqueueJob, drainQueue, errors } = asyncJobQueue({
    noAggregateErrors,
  });

  enqueueJob(memoizedLoadWithErrorAnnotation, [
    compartmentPrivateFields,
    moduleAliases,
    compartment,
    moduleSpecifier,
    enqueueJob,
    preferAsync,
    moduleLoads,
  ]);

  await drainQueue();

  throwAggregateError({
    errors,
    errorPrefix: `Failed to load module ${q(moduleSpecifier)} in package ${q(
      compartmentName,
    )}`,
  });
};

/**
 * `loadNow` synchronously gathers the module records for a specified module
 * and its transitive dependencies.
 * The module records refer to each other by a reference to the dependency's
 * compartment and the specifier of the module within its own compartment.
 * This graph is then ready to be synchronously linked and executed.
 * @param {WeakMap<Compartment, any>} compartmentPrivateFields
 * @param {WeakMap<object, object>} moduleAliases
 * @param {Compartment} compartment
 * @param {string} moduleSpecifier - The module specifier to load.
 * @param {{ noAggregateErrors?: boolean}} options
 */$h͏_once.load(load);

       const loadNow = (
  compartmentPrivateFields,
  moduleAliases,
  compartment,
  moduleSpecifier,
  { noAggregateErrors = false } = {},
) => {
  const { name: compartmentName } = weakmapGet(
    compartmentPrivateFields,
    compartment,
  );

  /** @type {Map<object, Map<string, Promise<Record<any, any>>>>} */
  const moduleLoads = new Map();

  const { enqueueJob, drainQueue, errors } = syncJobQueue({
    noAggregateErrors,
  });

  enqueueJob(memoizedLoadWithErrorAnnotation, [
    compartmentPrivateFields,
    moduleAliases,
    compartment,
    moduleSpecifier,
    enqueueJob,
    preferSync,
    moduleLoads,
  ]);

  drainQueue();

  throwAggregateError({
    errors,
    errorPrefix: `Failed to load module ${q(moduleSpecifier)} in package ${q(
      compartmentName,
    )}`,
  });
};$h͏_once.loadNow(loadNow);
})()
,
// === 46. ses ./src/module-proxy.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let makeAlias,Proxy,TypeError,create,freeze,mapGet,mapHas,mapSet,ownKeys,reflectGet,reflectGetOwnPropertyDescriptor,reflectHas,reflectIsExtensible,reflectPreventExtensions,toStringTagSymbol,weakmapSet,assert;$h͏_imports([["./module-load.js", [["makeAlias",[$h͏_a => (makeAlias = $h͏_a)]]]],["./commons.js", [["Proxy",[$h͏_a => (Proxy = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["mapGet",[$h͏_a => (mapGet = $h͏_a)]],["mapHas",[$h͏_a => (mapHas = $h͏_a)]],["mapSet",[$h͏_a => (mapSet = $h͏_a)]],["ownKeys",[$h͏_a => (ownKeys = $h͏_a)]],["reflectGet",[$h͏_a => (reflectGet = $h͏_a)]],["reflectGetOwnPropertyDescriptor",[$h͏_a => (reflectGetOwnPropertyDescriptor = $h͏_a)]],["reflectHas",[$h͏_a => (reflectHas = $h͏_a)]],["reflectIsExtensible",[$h͏_a => (reflectIsExtensible = $h͏_a)]],["reflectPreventExtensions",[$h͏_a => (reflectPreventExtensions = $h͏_a)]],["toStringTagSymbol",[$h͏_a => (toStringTagSymbol = $h͏_a)]],["weakmapSet",[$h͏_a => (weakmapSet = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);































const { quote: q } = assert;

// `deferExports` creates a module's exports proxy, proxied exports, and
// activator.
// A `Compartment` can create a module for any module specifier, regardless of
// whether it is loadable or executable, and use that object as a token that
// can be fed into another compartment's module map.
// Only after the specified module has been analyzed is it possible for the
// module namespace proxy to behave properly, so it throws exceptions until
// after the compartment has begun executing the module.
// The module instance must freeze the proxied exports and activate the exports
// proxy before executing the module.
//
// The module exports proxy's behavior differs from the ECMAScript 262
// specification for "module namespace exotic objects" only in that according
// to the specification value property descriptors have a non-writable "value"
// and this implementation models all properties with accessors.
//
// https://tc39.es/ecma262/#sec-module-namespace-exotic-objects
//
       const deferExports = () => {
  let active = false;
  const exportsTarget = create(null, {
    // Make this appear like an ESM module namespace object.
    [toStringTagSymbol]: {
      value: 'Module',
      writable: false,
      enumerable: false,
      configurable: false,
    },
  });
  return freeze({
    activate() {
      active = true;
    },
    exportsTarget,
    exportsProxy: new Proxy(exportsTarget, {
      get(_target, name, receiver) {
        if (!active) {
          throw TypeError(
            `Cannot get property ${q(
              name,
            )} of module exports namespace, the module has not yet begun to execute`,
          );
        }
        return reflectGet(exportsTarget, name, receiver);
      },
      set(_target, name, _value) {
        throw TypeError(
          `Cannot set property ${q(name)} of module exports namespace`,
        );
      },
      has(_target, name) {
        if (!active) {
          throw TypeError(
            `Cannot check property ${q(
              name,
            )}, the module has not yet begun to execute`,
          );
        }
        return reflectHas(exportsTarget, name);
      },
      deleteProperty(_target, name) {
        throw TypeError(
          `Cannot delete property ${q(name)}s of module exports namespace`,
        );
      },
      ownKeys(_target) {
        if (!active) {
          throw TypeError(
            'Cannot enumerate keys, the module has not yet begun to execute',
          );
        }
        return ownKeys(exportsTarget);
      },
      getOwnPropertyDescriptor(_target, name) {
        if (!active) {
          throw TypeError(
            `Cannot get own property descriptor ${q(
              name,
            )}, the module has not yet begun to execute`,
          );
        }
        return reflectGetOwnPropertyDescriptor(exportsTarget, name);
      },
      preventExtensions(_target) {
        if (!active) {
          throw TypeError(
            'Cannot prevent extensions of module exports namespace, the module has not yet begun to execute',
          );
        }
        return reflectPreventExtensions(exportsTarget);
      },
      isExtensible() {
        if (!active) {
          throw TypeError(
            'Cannot check extensibility of module exports namespace, the module has not yet begun to execute',
          );
        }
        return reflectIsExtensible(exportsTarget);
      },
      getPrototypeOf(_target) {
        return null;
      },
      setPrototypeOf(_target, _proto) {
        throw TypeError('Cannot set prototype of module exports namespace');
      },
      defineProperty(_target, name, _descriptor) {
        throw TypeError(
          `Cannot define property ${q(name)} of module exports namespace`,
        );
      },
      apply(_target, _thisArg, _args) {
        throw TypeError(
          'Cannot call module exports namespace, it is not a function',
        );
      },
      construct(_target, _args) {
        throw TypeError(
          'Cannot construct module exports namespace, it is not a constructor',
        );
      },
    }),
  });
};

/**
 * @typedef {object} DeferredExports
 * @property {Record<string, any>} exportsTarget - The object to which a
 * module's exports will be added.
 * @property {Record<string, any>} exportsProxy - A proxy over the `exportsTarget`,
 * used to expose its "exports" to other compartments.
 * @property {() => void} activate - Activate the `exportsProxy` such that it can
 * be used as a module namespace object.
 */

/**
 * Memoizes the creation of a deferred module exports namespace proxy for any
 * arbitrary full specifier in a compartment. It also records the compartment
 * and specifier affiliated with that module exports namespace proxy so it
 * can be used as an alias into another compartment when threaded through
 * a compartment's `moduleMap` argument.
 *
 * @param {*} compartment - The compartment to retrieve deferred exports from.
 * @param {*} compartmentPrivateFields - The private fields of the compartment.
 * @param {*} moduleAliases - The module aliases of the compartment.
 * @param {string} specifier - The module specifier to retrieve deferred exports for.
 * @returns {DeferredExports} - The deferred exports for the module specifier of
 * the compartment.
 */$h͏_once.deferExports(deferExports);
       const getDeferredExports = (
  compartment,
  compartmentPrivateFields,
  moduleAliases,
  specifier,
) => {
  const { deferredExports } = compartmentPrivateFields;
  if (!mapHas(deferredExports, specifier)) {
    const deferred = deferExports();
    weakmapSet(
      moduleAliases,
      deferred.exportsProxy,
      makeAlias(compartment, specifier),
    );
    mapSet(deferredExports, specifier, deferred);
  }
  return mapGet(deferredExports, specifier);
};$h͏_once.getDeferredExports(getDeferredExports);
})()
,
// === 47. ses ./src/compartment-evaluate.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let TypeError,arrayPush,create,getOwnPropertyDescriptors,evadeHtmlCommentTest,evadeImportExpressionTest,rejectSomeDirectEvalExpressions,makeSafeEvaluator;$h͏_imports([["./commons.js", [["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["arrayPush",[$h͏_a => (arrayPush = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]]]],["./transforms.js", [["evadeHtmlCommentTest",[$h͏_a => (evadeHtmlCommentTest = $h͏_a)]],["evadeImportExpressionTest",[$h͏_a => (evadeImportExpressionTest = $h͏_a)]],["rejectSomeDirectEvalExpressions",[$h͏_a => (rejectSomeDirectEvalExpressions = $h͏_a)]]]],["./make-safe-evaluator.js", [["makeSafeEvaluator",[$h͏_a => (makeSafeEvaluator = $h͏_a)]]]]]);













       const provideCompartmentEvaluator = (compartmentFields, options) => {
  const { sloppyGlobalsMode = false, __moduleShimLexicals__ = undefined } =
    options;

  let safeEvaluate;

  if (__moduleShimLexicals__ === undefined && !sloppyGlobalsMode) {
    ({ safeEvaluate } = compartmentFields);
  } else {
    // The scope proxy or global lexicals are different from the
    // shared evaluator so we need to build a new one

    let { globalTransforms } = compartmentFields;
    const { globalObject } = compartmentFields;

    let moduleLexicals;
    if (__moduleShimLexicals__ !== undefined) {
      // When using `evaluate` for ESM modules, as should only occur from the
      // module-shim's module-instance.js, we do not reveal the SES-shim's
      // module-to-program translation, as this is not standardizable behavior.
      // However, the `localTransforms` will come from the `__shimTransforms__`
      // Compartment option in this case, which is a non-standardizable escape
      // hatch so programs designed specifically for the SES-shim
      // implementation may opt-in to use the same transforms for `evaluate`
      // and `import`, at the expense of being tightly coupled to SES-shim.
      globalTransforms = undefined;

      moduleLexicals = create(
        null,
        getOwnPropertyDescriptors(__moduleShimLexicals__),
      );
    }

    ({ safeEvaluate } = makeSafeEvaluator({
      globalObject,
      moduleLexicals,
      globalTransforms,
      sloppyGlobalsMode,
    }));
  }

  return { safeEvaluate };
};$h͏_once.provideCompartmentEvaluator(provideCompartmentEvaluator);

       const compartmentEvaluate = (compartmentFields, source, options) => {
  // Perform this check first to avoid unnecessary sanitizing.
  // TODO Maybe relax string check and coerce instead:
  // https://github.com/tc39/proposal-dynamic-code-brand-checks
  if (typeof source !== 'string') {
    throw TypeError('first argument of evaluate() must be a string');
  }

  // Extract options, and shallow-clone transforms.
  const {
    transforms = [],
    __evadeHtmlCommentTest__ = false,
    __evadeImportExpressionTest__ = false,
    __rejectSomeDirectEvalExpressions__ = true  // Note default on
  } = options;
  const localTransforms = [...transforms];
  if (__evadeHtmlCommentTest__ === true) {
    arrayPush(localTransforms, evadeHtmlCommentTest);
  }
  if (__evadeImportExpressionTest__ === true) {
    arrayPush(localTransforms, evadeImportExpressionTest);
  }
  if (__rejectSomeDirectEvalExpressions__ === true) {
    arrayPush(localTransforms, rejectSomeDirectEvalExpressions);
  }

  const { safeEvaluate } = provideCompartmentEvaluator(
    compartmentFields,
    options,
  );

  return safeEvaluate(source, {
    localTransforms,
  });
};$h͏_once.compartmentEvaluate(compartmentEvaluate);
})()
,
// === 48. ses ./src/module-instance.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let assert,getDeferredExports,ReferenceError,SyntaxError,TypeError,arrayForEach,arrayIncludes,arrayPush,arraySome,arraySort,create,defineProperty,entries,freeze,isArray,keys,mapGet,weakmapGet,reflectHas,assign,compartmentEvaluate;$h͏_imports([["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]],["./module-proxy.js", [["getDeferredExports",[$h͏_a => (getDeferredExports = $h͏_a)]]]],["./commons.js", [["ReferenceError",[$h͏_a => (ReferenceError = $h͏_a)]],["SyntaxError",[$h͏_a => (SyntaxError = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["arrayForEach",[$h͏_a => (arrayForEach = $h͏_a)]],["arrayIncludes",[$h͏_a => (arrayIncludes = $h͏_a)]],["arrayPush",[$h͏_a => (arrayPush = $h͏_a)]],["arraySome",[$h͏_a => (arraySome = $h͏_a)]],["arraySort",[$h͏_a => (arraySort = $h͏_a)]],["create",[$h͏_a => (create = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["entries",[$h͏_a => (entries = $h͏_a)]],["freeze",[$h͏_a => (freeze = $h͏_a)]],["isArray",[$h͏_a => (isArray = $h͏_a)]],["keys",[$h͏_a => (keys = $h͏_a)]],["mapGet",[$h͏_a => (mapGet = $h͏_a)]],["weakmapGet",[$h͏_a => (weakmapGet = $h͏_a)]],["reflectHas",[$h͏_a => (reflectHas = $h͏_a)]],["assign",[$h͏_a => (assign = $h͏_a)]]]],["./compartment-evaluate.js", [["compartmentEvaluate",[$h͏_a => (compartmentEvaluate = $h͏_a)]]]]]);

























const { quote: q } = assert;

       const makeVirtualModuleInstance = (
  compartmentPrivateFields,
  moduleSource,
  compartment,
  moduleAliases,
  moduleSpecifier,
  resolvedImports,
) => {
  const { exportsProxy, exportsTarget, activate } = getDeferredExports(
    compartment,
    weakmapGet(compartmentPrivateFields, compartment),
    moduleAliases,
    moduleSpecifier,
  );

  const notifiers = create(null);

  if (moduleSource.exports) {
    if (
      !isArray(moduleSource.exports) ||
      arraySome(moduleSource.exports, name => typeof name !== 'string')
    ) {
      throw TypeError(
        `SES virtual module source "exports" property must be an array of strings for module ${moduleSpecifier}`,
      );
    }
    arrayForEach(moduleSource.exports, name => {
      let value = exportsTarget[name];
      const updaters = [];

      const get = () => value;

      const set = newValue => {
        value = newValue;
        for (const updater of updaters) {
          updater(newValue);
        }
      };

      defineProperty(exportsTarget, name, {
        get,
        set,
        enumerable: true,
        configurable: false,
      });

      notifiers[name] = update => {
        arrayPush(updaters, update);
        update(value);
      };
    });
    // This is enough to support import * from cjs - the '*' field doesn't need to be in exports nor exportsTarget because import will only ever access it via notifiers
    notifiers['*'] = update => {
      update(exportsTarget);
    };
  }

  const localState = {
    activated: false,
  };
  return freeze({
    notifiers,
    exportsProxy,
    execute() {
      if (reflectHas(localState, 'errorFromExecute')) {
        throw localState.errorFromExecute;
      }
      if (!localState.activated) {
        activate();
        localState.activated = true;
        try {
          // eslint-disable-next-line @endo/no-polymorphic-call
          moduleSource.execute(exportsTarget, compartment, resolvedImports);
        } catch (err) {
          localState.errorFromExecute = err;
          throw err;
        }
      }
    },
  });
};

// `makeModuleInstance` takes a module's compartment record, the live import
// namespace, and a global object; and produces a module instance.
// The module instance carries the proxied module exports namespace (the
// "exports"), notifiers to update the module's internal import namespace, and
// an idempotent execute function.
// The module exports namespace is a proxy to the proxied exports namespace
// that the execution of the module instance populates.
$h͏_once.makeVirtualModuleInstance(makeVirtualModuleInstance);const makeModuleInstance=(
  privateFields,
  moduleAliases,
  moduleRecord,
  importedInstances,
) => {
  const {
    compartment,
    moduleSpecifier,
    moduleSource,
    importMeta: moduleRecordMeta,
  } = moduleRecord;
  const {
    reexports: exportAlls = [],
    __syncModuleProgram__: functorSource,
    __fixedExportMap__: fixedExportMap = {},
    __liveExportMap__: liveExportMap = {},
    __reexportMap__: reexportMap = {},
    __needsImport__: needsImport = false,
    __needsImportMeta__: needsImportMeta = false,
    __syncModuleFunctor__,
  } = moduleSource;

  const compartmentFields = weakmapGet(privateFields, compartment);

  const { __shimTransforms__, resolveHook, importMetaHook, compartmentImport } =
    compartmentFields;

  const { exportsProxy, exportsTarget, activate } = getDeferredExports(
    compartment,
    compartmentFields,
    moduleAliases,
    moduleSpecifier,
  );

  // {_exportName_: getter} module exports namespace
  // object (eventually proxied).
  const exportsProps = create(null);

  // {_localName_: accessor} proxy traps for moduleLexicals and live bindings.
  // The moduleLexicals object is frozen and the corresponding properties of
  // moduleLexicals must be immutable, so we copy the descriptors.
  const moduleLexicals = create(null);

  // {_localName_: init(initValue) -> initValue} used by the
  // rewritten code to initialize exported fixed bindings.
  const onceVar = create(null);

  // {_localName_: update(newValue)} used by the rewritten code to
  // both initialize and update live bindings.
  const liveVar = create(null);

  const importMeta = create(null);
  if (moduleRecordMeta) {
    assign(importMeta, moduleRecordMeta);
  }
  if (needsImportMeta && importMetaHook) {
    importMetaHook(moduleSpecifier, importMeta);
  }

  /** @type {(fullSpecifier: string) => Promise<ModuleExportsNamespace>} */
  let dynamicImport;
  if (needsImport) {
    /** @param {string} importSpecifier */
    dynamicImport = async importSpecifier =>
      compartmentImport(resolveHook(importSpecifier, moduleSpecifier));
  }

  // {_localName_: [{get, set, notify}]} used to merge all the export updaters.
  const localGetNotify = create(null);

  // {[importName: string]: notify(update(newValue))} Used by code that imports
  // one of this module's exports, so that their update function will
  // be notified when this binding is initialized or updated.
  const notifiers = create(null);

  arrayForEach(entries(fixedExportMap), ([fixedExportName, [localName]]) => {
    let fixedGetNotify = localGetNotify[localName];
    if (!fixedGetNotify) {
      // fixed binding state
      let value;
      let tdz = true;
      /** @type {null | Array<(value: any) => void>} */
      let optUpdaters = [];

      // tdz sensitive getter
      const get = () => {
        if (tdz) {
          throw ReferenceError(`binding ${q(localName)} not yet initialized`);
        }
        return value;
      };

      // leave tdz once
      const init = freeze(initValue => {
        // init with initValue of a declared const binding, and return
        // it.
        if (!tdz) {
          throw TypeError(
            `Internal: binding ${q(localName)} already initialized`,
          );
        }
        value = initValue;
        const updaters = optUpdaters;
        optUpdaters = null;
        tdz = false;
        for (const updater of updaters || []) {
          updater(initValue);
        }
        return initValue;
      });

      // If still tdz, register update for notification later.
      // Otherwise, update now.
      const notify = updater => {
        if (updater === init) {
          // Prevent recursion.
          return;
        }
        if (tdz) {
          arrayPush(optUpdaters || [], updater);
        } else {
          updater(value);
        }
      };

      // Need these for additional exports of the local variable.
      fixedGetNotify = {
        get,
        notify,
      };
      localGetNotify[localName] = fixedGetNotify;
      onceVar[localName] = init;
    }

    exportsProps[fixedExportName] = {
      get: fixedGetNotify.get,
      set: undefined,
      enumerable: true,
      configurable: false,
    };

    notifiers[fixedExportName] = fixedGetNotify.notify;
  });

  arrayForEach(
    entries(liveExportMap),
    ([liveExportName, [localName, setProxyTrap]]) => {
      let liveGetNotify = localGetNotify[localName];
      if (!liveGetNotify) {
        // live binding state
        let value;
        let tdz = true;
        const updaters = [];

        // tdz sensitive getter
        const get = () => {
          if (tdz) {
            throw ReferenceError(
              `binding ${q(liveExportName)} not yet initialized`,
            );
          }
          return value;
        };

        // This must be usable locally for the translation of initializing
        // a declared local live binding variable.
        //
        // For reexported variable, this is also an update function to
        // register for notification with the downstream import, which we
        // must assume to be live. Thus, it can be called independent of
        // tdz but always leaves tdz. Such reexporting creates a tree of
        // bindings. This lets the tree be hooked up even if the imported
        // module instance isn't initialized yet, as may happen in cycles.
        const update = freeze(newValue => {
          value = newValue;
          tdz = false;
          for (const updater of updaters) {
            updater(newValue);
          }
        });

        // tdz sensitive setter
        const set = newValue => {
          if (tdz) {
            throw ReferenceError(`binding ${q(localName)} not yet initialized`);
          }
          value = newValue;
          for (const updater of updaters) {
            updater(newValue);
          }
        };

        // Always register the updater function.
        // If not in tdz, also update now.
        const notify = updater => {
          if (updater === update) {
            // Prevent recursion.
            return;
          }
          arrayPush(updaters, updater);
          if (!tdz) {
            updater(value);
          }
        };

        liveGetNotify = {
          get,
          notify,
        };

        localGetNotify[localName] = liveGetNotify;
        if (setProxyTrap) {
          defineProperty(moduleLexicals, localName, {
            get,
            set,
            enumerable: true,
            configurable: false,
          });
        }
        liveVar[localName] = update;
      }

      exportsProps[liveExportName] = {
        get: liveGetNotify.get,
        set: undefined,
        enumerable: true,
        configurable: false,
      };

      notifiers[liveExportName] = liveGetNotify.notify;
    },
  );

  const notifyStar = update => {
    update(exportsTarget);
  };
  notifiers['*'] = notifyStar;

  const wireUpExportNotifier = (exportName, notify) => {
    if (!notifiers[exportName] && notify !== false) {
      notifiers[exportName] = notify;

      // exported live binding state
      let value;
      const update = newValue => (value = newValue);
      notify(update);
      exportsProps[exportName] = {
        get() {
          return value;
        },
        set: undefined,
        enumerable: true,
        configurable: false,
      };
    }
  };

  // Per the calling convention for the moduleFunctor generated from
  // an ESM, the `imports` function gets called once up front
  // to populate or arrange the population of imports and reexports.
  // The generated code produces an `updateRecord`: the means for
  // the linker to update the imports and exports of the module.
  // The updateRecord must conform to moduleAnalysis.imports
  // updateRecord = Map<specifier, importUpdaters>
  // importUpdaters = Map<importName, [update(newValue)*]>
  function imports(updateRecord) {
    // By the time imports is called, the importedInstances should already be
    // initialized with module instances that satisfy
    // imports.
    // importedInstances = Map[_specifier_, { notifiers, module, execute }]
    // notifiers = { [importName: string]: notify(update(newValue))}

    // export * cannot export default.
    const candidateAll = create(null);
    candidateAll.default = false;
    for (const [specifier, importUpdaters] of updateRecord) {
      const instance = mapGet(importedInstances, specifier);
      // The module instance object is an internal literal, does not bind this,
      // and never revealed outside the SES shim.
      // There are two instantiation sites for instances and they are both in
      // this module.
      // eslint-disable-next-line @endo/no-polymorphic-call
      instance.execute(); // bottom up cycle tolerant
      const { notifiers: importNotifiers } = instance;
      for (const [importName, updaters] of importUpdaters) {
        const importNotify = importNotifiers[importName];
        if (!importNotify) {
          throw SyntaxError(
            `The requested module '${specifier}' does not provide an export named '${importName}'`,
          );
        }
        for (const updater of updaters) {
          importNotify(updater);
        }
      }
      if (arrayIncludes(exportAlls, specifier)) {
        // Make all these imports candidates.
        // Note names don't change in reexporting all
        for (const [importAndExportName, importNotify] of entries(
          importNotifiers,
        )) {
          if (candidateAll[importAndExportName] === undefined) {
            candidateAll[importAndExportName] = importNotify;
          } else {
            // Already a candidate: remove ambiguity.
            candidateAll[importAndExportName] = false;
          }
        }
      }
      if (reexportMap[specifier]) {
        // Set up reexport notifiers instantly so they are available in cycles.
        for (const [localName, exportedName] of reexportMap[specifier]) {
          wireUpExportNotifier(exportedName, importNotifiers[localName]);
        }
      }
    }

    for (const [exportName, notify] of entries(candidateAll)) {
      wireUpExportNotifier(exportName, notify);
    }

    // Sort the module exports namespace as per spec.
    // The module exports namespace will be wrapped in a module namespace
    // exports proxy which will serve as a "module exports namespace exotic
    // object".
    // Sorting properties is not generally reliable because some properties may
    // be symbols, and symbols do not have an inherent relative order, but
    // since all properties of the exports namespace must be keyed by a string
    // and the string must correspond to a valid identifier, sorting these
    // properties works for this specific case.
    arrayForEach(arraySort(keys(exportsProps)), k =>
      defineProperty(exportsTarget, k, exportsProps[k]),
    );

    freeze(exportsTarget);
    activate();
  }

  let optFunctor;
  if (__syncModuleFunctor__ !== undefined) {
    optFunctor = __syncModuleFunctor__;
  } else {
    optFunctor = compartmentEvaluate(compartmentFields, functorSource, {
      globalObject: compartment.globalThis,
      transforms: __shimTransforms__,
      __moduleShimLexicals__: moduleLexicals,
    });
  }
  let didThrow = false;
  let thrownError;
  function execute() {
    if (optFunctor) {
      // uninitialized
      const functor = optFunctor;
      optFunctor = null;
      // initializing - call with `this` of `undefined`.
      try {
        functor(
          freeze({
            imports: freeze(imports),
            onceVar: freeze(onceVar),
            liveVar: freeze(liveVar),
            import: dynamicImport,
            importMeta,
          }),
        );
      } catch (e) {
        didThrow = true;
        thrownError = e;
      }
      // initialized
    }
    if (didThrow) {
      throw thrownError;
    }
  }

  return freeze({
    notifiers,
    exportsProxy,
    execute,
  });
};$h͏_once.makeModuleInstance(makeModuleInstance);
})()
,
// === 49. ses ./src/module-link.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let assert,makeModuleInstance,makeVirtualModuleInstance,Map,ReferenceError,TypeError,entries,isArray,isPrimitive,mapGet,mapHas,mapSet,weakmapGet;$h͏_imports([["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]],["./module-instance.js", [["makeModuleInstance",[$h͏_a => (makeModuleInstance = $h͏_a)]],["makeVirtualModuleInstance",[$h͏_a => (makeVirtualModuleInstance = $h͏_a)]]]],["./commons.js", [["Map",[$h͏_a => (Map = $h͏_a)]],["ReferenceError",[$h͏_a => (ReferenceError = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["entries",[$h͏_a => (entries = $h͏_a)]],["isArray",[$h͏_a => (isArray = $h͏_a)]],["isPrimitive",[$h͏_a => (isPrimitive = $h͏_a)]],["mapGet",[$h͏_a => (mapGet = $h͏_a)]],["mapHas",[$h͏_a => (mapHas = $h͏_a)]],["mapSet",[$h͏_a => (mapSet = $h͏_a)]],["weakmapGet",[$h͏_a => (weakmapGet = $h͏_a)]]]]]);



















const { Fail, quote: q } = assert;

// `link` creates `ModuleInstances` and `ModuleNamespaces` for a module and its
// transitive dependencies and connects their imports and exports.
// After linking, the resulting working set is ready to be executed.
// The linker only concerns itself with module namespaces that are objects with
// property descriptors for their exports, which the Compartment proxies with
// the actual `ModuleNamespace`.
       const link = (
  compartmentPrivateFields,
  moduleAliases,
  compartment,
  moduleSpecifier,
) => {
  const { name: compartmentName, moduleRecords } = weakmapGet(
    compartmentPrivateFields,
    compartment,
  );

  const moduleRecord = mapGet(moduleRecords, moduleSpecifier);
  if (moduleRecord === undefined) {
    throw ReferenceError(
      `Missing link to module ${q(moduleSpecifier)} from compartment ${q(
        compartmentName,
      )}`,
    );
  }

  // Mutual recursion so there's no confusion about which
  // compartment is in context: the module record may be in another
  // compartment, denoted by moduleRecord.compartment.
  // eslint-disable-next-line no-use-before-define
  return instantiate(compartmentPrivateFields, moduleAliases, moduleRecord);
};$h͏_once.link(link);

function mayBePrecompiledModuleSource(moduleSource) {
  return typeof moduleSource.__syncModuleProgram__ === 'string';
}

function validatePrecompiledModuleSource(moduleSource, moduleSpecifier) {
  const { __fixedExportMap__, __liveExportMap__ } = moduleSource;
  !isPrimitive(__fixedExportMap__) ||
    Fail`Property '__fixedExportMap__' of a precompiled module source must be an object, got ${q(
      __fixedExportMap__,
    )}, for module ${q(moduleSpecifier)}`;
  !isPrimitive(__liveExportMap__) ||
    Fail`Property '__liveExportMap__' of a precompiled module source must be an object, got ${q(
      __liveExportMap__,
    )}, for module ${q(moduleSpecifier)}`;
}

function mayBeVirtualModuleSource(moduleSource) {
  return typeof moduleSource.execute === 'function';
}

function validateVirtualModuleSource(moduleSource, moduleSpecifier) {
  const { exports } = moduleSource;
  isArray(exports) ||
    Fail`Invalid module source: 'exports' of a virtual module source must be an array, got ${q(
      exports,
    )}, for module ${q(moduleSpecifier)}`;
}

function validateModuleSource(moduleSource, moduleSpecifier) {
  !isPrimitive(moduleSource) ||
    Fail`Invalid module source: must be of type object, got ${q(
      moduleSource,
    )}, for module ${q(moduleSpecifier)}`;
  const { imports, exports, reexports = [] } = moduleSource;
  isArray(imports) ||
    Fail`Invalid module source: 'imports' must be an array, got ${q(
      imports,
    )}, for module ${q(moduleSpecifier)}`;
  isArray(exports) ||
    Fail`Invalid module source: 'exports' must be an array, got ${q(
      exports,
    )}, for module ${q(moduleSpecifier)}`;
  isArray(reexports) ||
    Fail`Invalid module source: 'reexports' must be an array if present, got ${q(
      reexports,
    )}, for module ${q(moduleSpecifier)}`;
}

       const instantiate = (
  compartmentPrivateFields,
  moduleAliases,
  moduleRecord,
) => {
  const { compartment, moduleSpecifier, resolvedImports, moduleSource } =
    moduleRecord;
  const { instances } = weakmapGet(compartmentPrivateFields, compartment);

  // Memoize.
  if (mapHas(instances, moduleSpecifier)) {
    return mapGet(instances, moduleSpecifier);
  }

  validateModuleSource(moduleSource, moduleSpecifier);

  const importedInstances = new Map();
  let moduleInstance;
  if (mayBePrecompiledModuleSource(moduleSource)) {
    validatePrecompiledModuleSource(moduleSource, moduleSpecifier);
    moduleInstance = makeModuleInstance(
      compartmentPrivateFields,
      moduleAliases,
      moduleRecord,
      importedInstances,
    );
  } else if (mayBeVirtualModuleSource(moduleSource)) {
    validateVirtualModuleSource(moduleSource, moduleSpecifier);
    moduleInstance = makeVirtualModuleInstance(
      compartmentPrivateFields,
      moduleSource,
      compartment,
      moduleAliases,
      moduleSpecifier,
      resolvedImports,
    );
  } else {
    throw TypeError(`Invalid module source, got ${q(moduleSource)}`);
  }

  // Memoize.
  mapSet(instances, moduleSpecifier, moduleInstance);

  // Link dependency modules.
  for (const [importSpecifier, resolvedSpecifier] of entries(resolvedImports)) {
    const importedInstance = link(
      compartmentPrivateFields,
      moduleAliases,
      compartment,
      resolvedSpecifier,
    );
    mapSet(importedInstances, importSpecifier, importedInstance);
  }

  return moduleInstance;
};$h͏_once.instantiate(instantiate);
})()
,
// === 50. ses ./src/compartment.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Map,TypeError,WeakMap,arrayFlatMap,assign,defineProperties,identity,promiseThen,toStringTagSymbol,weakmapGet,weakmapSet,setGlobalObjectSymbolUnscopables,setGlobalObjectConstantProperties,setGlobalObjectMutableProperties,setGlobalObjectEvaluators,assert,assertEqual,q,sharedGlobalPropertyNames,load,loadNow,link,getDeferredExports,compartmentEvaluate,makeSafeEvaluator;$h͏_imports([["./commons.js", [["Map",[$h͏_a => (Map = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["WeakMap",[$h͏_a => (WeakMap = $h͏_a)]],["arrayFlatMap",[$h͏_a => (arrayFlatMap = $h͏_a)]],["assign",[$h͏_a => (assign = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["identity",[$h͏_a => (identity = $h͏_a)]],["promiseThen",[$h͏_a => (promiseThen = $h͏_a)]],["toStringTagSymbol",[$h͏_a => (toStringTagSymbol = $h͏_a)]],["weakmapGet",[$h͏_a => (weakmapGet = $h͏_a)]],["weakmapSet",[$h͏_a => (weakmapSet = $h͏_a)]]]],["./global-object.js", [["setGlobalObjectSymbolUnscopables",[$h͏_a => (setGlobalObjectSymbolUnscopables = $h͏_a)]],["setGlobalObjectConstantProperties",[$h͏_a => (setGlobalObjectConstantProperties = $h͏_a)]],["setGlobalObjectMutableProperties",[$h͏_a => (setGlobalObjectMutableProperties = $h͏_a)]],["setGlobalObjectEvaluators",[$h͏_a => (setGlobalObjectEvaluators = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]],["assertEqual",[$h͏_a => (assertEqual = $h͏_a)]],["q",[$h͏_a => (q = $h͏_a)]]]],["./permits.js", [["sharedGlobalPropertyNames",[$h͏_a => (sharedGlobalPropertyNames = $h͏_a)]]]],["./module-load.js", [["load",[$h͏_a => (load = $h͏_a)]],["loadNow",[$h͏_a => (loadNow = $h͏_a)]]]],["./module-link.js", [["link",[$h͏_a => (link = $h͏_a)]]]],["./module-proxy.js", [["getDeferredExports",[$h͏_a => (getDeferredExports = $h͏_a)]]]],["./compartment-evaluate.js", [["compartmentEvaluate",[$h͏_a => (compartmentEvaluate = $h͏_a)]]]],["./make-safe-evaluator.js", [["makeSafeEvaluator",[$h͏_a => (makeSafeEvaluator = $h͏_a)]]]]]);




































































/**
 * @import {ImportHook, ImportMetaHook, ImportNowHook, ModuleDescriptor, ModuleExportsNamespace, ModuleMap, ModuleMapHook, ResolveHook, ModuleSource, CompartmentOptions} from '../types.js'
 * @import {Transform} from './lockdown.js'
 * @import {DeferredExports} from './module-proxy.js'
 */

/**
 * Associates every public module exports namespace with its corresponding
 * compartment and specifier so they can be used to link modules across
 * compartments. The mechanism to thread an alias is to use the
 * {@link Compartment.module} function to obtain the exports namespace of a foreign
 * module and pass it into another compartment's `moduleMap` constructor option
 * @type {WeakMap<ModuleExportsNamespace, Compartment>}
 *
 */
const moduleAliases = new WeakMap();

/**
 * Private fields for `Compartment` instances
 * @typedef {object} CompartmentFields
 * @property {string} name
 * @property {object} globalObject
 * @property {Array<Transform>} globalTransforms
 * @property {(source: string, options?: {localTransforms?: Array<Transform>}) => void} safeEvaluate
 * @property {ResolveHook} resolveHook
 * @property {ImportHook} importHook
 * @property {ImportNowHook} importNowHook
 * @property {ModuleMap} moduleMap
 * @property {ModuleMapHook} moduleMapHook
 * @property {ImportMetaHook} importMetaHook
 * @property {Map<string, ModuleSource>} moduleRecords
 * @property {Array<Transform>} __shimTransforms__
 * @property {DeferredExports} deferredExports
 * @property {Map<string, ModuleDescriptor>} instances
 * @property {Compartment} [parentCompartment]
 * @property {boolean} noNamespaceBox
 * @property {(fullSpecifier: string) => Promise<ModuleExportsNamespace>} compartmentImport
 * @property {boolean} [noAggregateLoadErrors]
 */

/**
 * Captures the private state for each {@link Compartment}
 * @type {WeakMap<Compartment, CompartmentFields>}
 */
const privateFields = new WeakMap();

       const InertCompartment = function Compartment(
  _endowments = {},
  _modules = {},
  _options = {},
) {
  throw TypeError(
    'Compartment.prototype.constructor is not a valid constructor.',
  );
};

/**
 * @param {Compartment} compartment
 * @param {string} specifier
 * @returns {{namespace: ModuleExportsNamespace}}
 */$h͏_once.InertCompartment(InertCompartment);
const compartmentImportNow = (compartment, specifier) => {
  const { execute, exportsProxy } = link(
    privateFields,
    moduleAliases,
    compartment,
    specifier,
  );
  execute();
  return exportsProxy;
};

/** @type {Compartment & {constructor: typeof InertCompartment}} */
       const CompartmentPrototype = {
  constructor: InertCompartment,

  get globalThis() {
    return /** @type {CompartmentFields} */ (weakmapGet(privateFields, this))
      .globalObject;
  },

  get name() {
    return /** @type {CompartmentFields} */ (weakmapGet(privateFields, this))
      .name;
  },

  evaluate(source, options = {}) {
    const compartmentFields = weakmapGet(privateFields, this);
    return compartmentEvaluate(compartmentFields, source, options);
  },

  module(specifier) {
    if (typeof specifier !== 'string') {
      throw TypeError('first argument of module() must be a string');
    }

    const { exportsProxy } = getDeferredExports(
      this,
      weakmapGet(privateFields, this),
      moduleAliases,
      specifier,
    );

    return exportsProxy;
  },

  async import(specifier) {
    const { noNamespaceBox, noAggregateLoadErrors } =
      /** @type {CompartmentFields} */ (weakmapGet(privateFields, this));

    if (typeof specifier !== 'string') {
      throw TypeError('first argument of import() must be a string');
    }

    return promiseThen(
      load(privateFields, moduleAliases, this, specifier, {
        noAggregateErrors: noAggregateLoadErrors,
      }),
      () => {
        // The namespace box is a contentious design and likely to be a breaking
        // change in an appropriately numbered future version.
        const namespace = compartmentImportNow(
          /** @type {Compartment} */ (this),
          specifier,
        );
        if (noNamespaceBox) {
          return namespace;
        }
        // Legacy behavior: box the namespace object so that thenable modules
        // do not get coerced into a promise accidentally.
        return { namespace };
      },
    );
  },

  async load(specifier) {
    if (typeof specifier !== 'string') {
      throw TypeError('first argument of load() must be a string');
    }

    const { noAggregateLoadErrors } = /** @type {CompartmentFields} */ (
      weakmapGet(privateFields, this)
    );

    return load(privateFields, moduleAliases, this, specifier, {
      noAggregateErrors: noAggregateLoadErrors,
    });
  },

  importNow(specifier) {
    if (typeof specifier !== 'string') {
      throw TypeError('first argument of importNow() must be a string');
    }
    const { noAggregateLoadErrors } = /** @type {CompartmentFields} */ (
      weakmapGet(privateFields, this)
    );

    loadNow(privateFields, moduleAliases, this, specifier, {
      noAggregateErrors: noAggregateLoadErrors,
    });
    return compartmentImportNow(/** @type {Compartment} */ (this), specifier);
  },
};

// This causes `String(new Compartment())` to evaluate to `[object Compartment]`.
// The descriptor follows the conventions of other globals with @@toStringTag
// properties, e.g. Math.
$h͏_once.CompartmentPrototype(CompartmentPrototype);defineProperties(CompartmentPrototype,{
  [toStringTagSymbol]: {
    value: 'Compartment',
    writable: false,
    enumerable: false,
    configurable: true,
  },
});

defineProperties(InertCompartment, {
  prototype: { value: CompartmentPrototype },
});

/**
 * @callback MakeCompartmentConstructor
 * @param {MakeCompartmentConstructor} targetMakeCompartmentConstructor
 * @param {Record<string, any>} intrinsics
 * @param {(object: object) => void} markVirtualizedNativeFunction
 * @param {object} [options]
 * @param {Compartment} [options.parentCompartment]
 * @param {boolean} [options.enforceNew]
 * @returns {Compartment['constructor']}
 */

/**
 * "Options bag"-style `Compartment` constructor arguments.
 * @typedef {[options?: CompartmentOptions & { __options__: true }]} CompartmentOptionsArgs
 */

/**
 * Legacy `Compartment` constructor arguments.
 *
 * @deprecated
 * @typedef {[globals?: Map<string, any>, modules?: Map<string, ModuleDescriptor>, options?: CompartmentOptions]} LegacyCompartmentOptionsArgs
 */

/**
 * In order to facilitate migration from the deprecated signature of the
 * compartment constructor,
 *
 * `new Compartent(globals?, modules?, options?)`
 *
 * to the new signature:
 *
 * `new Compartment(options?)`
 *
 * ...where globals and modules are expressed in the options bag instead of
 * positional arguments, this function detects the temporary sigil __options__
 * on the first argument and coerces compartments arguments into a single
 * compartments object.
 * @param {CompartmentOptionsArgs|LegacyCompartmentOptionsArgs} args
 * @returns {CompartmentOptions}
 */
       const compartmentOptions = (...args) => {
  if (args.length === 0) {
    return {};
  }
  if (
    args.length === 1 &&
    typeof args[0] === 'object' &&
    args[0] !== null &&
    '__options__' in args[0]
  ) {
    const { __options__, ...options } = args[0];
    assert(
      __options__ === true,
      `Compartment constructor only supports true __options__ sigil, got ${__options__}`,
    );
    return options;
  } else {
    const [
      globals = /** @type {Map<string, any>} */ ({}),
      modules = /** @type {Map<string, ModuleDescriptor>} */ ({}),
      options = {},
    ] = /** @type {LegacyCompartmentOptionsArgs} */ (args);
    assertEqual(
      options.modules,
      undefined,
      `Compartment constructor must receive either a module map argument or modules option, not both`,
    );
    assertEqual(
      options.globals,
      undefined,
      `Compartment constructor must receive either globals argument or option, not both`,
    );
    return {
      ...options,
      globals,
      modules,
    };
  }
};

/** @type {MakeCompartmentConstructor} */$h͏_once.compartmentOptions(compartmentOptions);
       const makeCompartmentConstructor = (
  targetMakeCompartmentConstructor,
  intrinsics,
  markVirtualizedNativeFunction,
  { parentCompartment = undefined, enforceNew = false } = {},
) => {
  /**
   *
   * @param {CompartmentOptionsArgs|LegacyCompartmentOptionsArgs} args
   */
  function Compartment(...args) {
    if (enforceNew && new.target === undefined) {
      throw TypeError(
        "Class constructor Compartment cannot be invoked without 'new'",
      );
    }

    // Extract options, and shallow-clone transforms.
    const {
      name = '<unknown>',
      transforms = [],
      __shimTransforms__ = [],
      globals: endowmentsOption = {},
      modules: moduleMapOption = {},
      resolveHook,
      importHook,
      importNowHook,
      moduleMapHook,
      importMetaHook,
      __noNamespaceBox__: noNamespaceBox = false,
      noAggregateLoadErrors = false,
    } = compartmentOptions(...args);
    const globalTransforms = arrayFlatMap(
      [transforms, __shimTransforms__],
      identity,
    );
    const endowments = { __proto__: null, ...endowmentsOption };
    const moduleMap = { __proto__: null, ...moduleMapOption };

    // Map<FullSpecifier, ModuleCompartmentRecord>
    const moduleRecords = new Map();
    // Map<FullSpecifier, ModuleInstance>
    const instances = new Map();
    // Map<FullSpecifier, {ExportsProxy, ProxiedExports, activate()}>
    const deferredExports = new Map();

    const globalObject = {};

    const compartment = this;

    setGlobalObjectSymbolUnscopables(globalObject);

    // We must initialize all constant properties first because
    // `makeSafeEvaluator` may use them to create optimized bindings
    // in the evaluator.
    // TODO: consider merging into a single initialization if internal
    // evaluator is no longer eagerly created
    setGlobalObjectConstantProperties(globalObject);

    const { safeEvaluate } = makeSafeEvaluator({
      globalObject,
      globalTransforms,
      sloppyGlobalsMode: false,
    });

    setGlobalObjectMutableProperties(globalObject, {
      intrinsics,
      newGlobalPropertyNames: sharedGlobalPropertyNames,
      makeCompartmentConstructor: targetMakeCompartmentConstructor,
      parentCompartment: this,
      markVirtualizedNativeFunction,
    });

    // TODO: maybe add evalTaming to the Compartment constructor 3rd options?
    setGlobalObjectEvaluators(
      globalObject,
      safeEvaluate,
      markVirtualizedNativeFunction,
    );

    assign(globalObject, endowments);

    /**
     * In support dynamic import in a module source loaded by this compartment,
     * like `await import(importSpecifier)`, induces this compartment to import
     * a module, returning a promise for the resulting module exports
     * namespace.
     * Unlike `compartment.import`, never creates a box object for the
     * namespace as that behavior is deprecated and inconsistent with the
     * standard behavior of dynamic import.
     * Obliges the caller to resolve import specifiers to their corresponding
     * full specifier.
     * That is, every module must have its own dynamic import function that
     * closes over the surrounding module's full module specifier and calls
     * through to this function.
     * @param {string} fullSpecifier - A full specifier is a key in the
     * compartment's module memo.
     * The method `compartment.import` accepts a full specifier, but dynamic
     * import accepts an import specifier and resolves it to a full specifier
     * relative to the calling module's full specifier.
     * @returns {Promise<ModuleExportsNamespace>}
     */
    const compartmentImport = async fullSpecifier => {
      if (typeof resolveHook !== 'function') {
        throw TypeError(
          `Compartment does not support dynamic import: no configured resolveHook for compartment ${q(name)}`,
        );
      }
      await load(privateFields, moduleAliases, compartment, fullSpecifier, {
        noAggregateErrors: noAggregateLoadErrors,
      });
      const { execute, exportsProxy } = link(
        privateFields,
        moduleAliases,
        compartment,
        fullSpecifier,
      );
      execute();
      return exportsProxy;
    };

    weakmapSet(privateFields, this, {
      name: `${name}`,
      globalTransforms,
      globalObject,
      safeEvaluate,
      resolveHook,
      importHook,
      importNowHook,
      moduleMap,
      moduleMapHook,
      importMetaHook,
      moduleRecords,
      __shimTransforms__,
      deferredExports,
      instances,
      parentCompartment,
      noNamespaceBox,
      compartmentImport,
      noAggregateLoadErrors,
    });
  }

  Compartment.prototype = CompartmentPrototype;

  return Compartment;
};$h͏_once.makeCompartmentConstructor(makeCompartmentConstructor);
})()
,
// === 51. ses ./src/get-anonymous-intrinsics.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let FERAL_FUNCTION,Float32Array,Map,Set,String,getOwnPropertyDescriptor,getPrototypeOf,iterateArray,iterateMap,iterateSet,iterateString,matchAllRegExp,matchAllSymbol,regexpPrototype,globalThis,assign,AsyncGeneratorFunctionInstance,ArrayBuffer,InertCompartment;$h͏_imports([["./commons.js", [["FERAL_FUNCTION",[$h͏_a => (FERAL_FUNCTION = $h͏_a)]],["Float32Array",[$h͏_a => (Float32Array = $h͏_a)]],["Map",[$h͏_a => (Map = $h͏_a)]],["Set",[$h͏_a => (Set = $h͏_a)]],["String",[$h͏_a => (String = $h͏_a)]],["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["getPrototypeOf",[$h͏_a => (getPrototypeOf = $h͏_a)]],["iterateArray",[$h͏_a => (iterateArray = $h͏_a)]],["iterateMap",[$h͏_a => (iterateMap = $h͏_a)]],["iterateSet",[$h͏_a => (iterateSet = $h͏_a)]],["iterateString",[$h͏_a => (iterateString = $h͏_a)]],["matchAllRegExp",[$h͏_a => (matchAllRegExp = $h͏_a)]],["matchAllSymbol",[$h͏_a => (matchAllSymbol = $h͏_a)]],["regexpPrototype",[$h͏_a => (regexpPrototype = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["assign",[$h͏_a => (assign = $h͏_a)]],["AsyncGeneratorFunctionInstance",[$h͏_a => (AsyncGeneratorFunctionInstance = $h͏_a)]],["ArrayBuffer",[$h͏_a => (ArrayBuffer = $h͏_a)]]]],["./compartment.js", [["InertCompartment",[$h͏_a => (InertCompartment = $h͏_a)]]]]]);





















/**
 * Object.getConstructorOf()
 * Helper function to improve readability, similar to Object.getPrototypeOf().
 *
 * @param {object} obj
 */
function getConstructorOf(obj) {
  return getPrototypeOf(obj).constructor;
}

// getAnonymousIntrinsics uses a utility function to construct an arguments
// object, since it cannot have one of its own and also be a const export.
function makeArguments() {
  // eslint-disable-next-line prefer-rest-params
  return arguments;
}

/**
 * getAnonymousIntrinsics()
 * Get the intrinsics not otherwise reachable by named own property
 * traversal from the global object.
 *
 * @returns {object}
 */
       const getAnonymousIntrinsics = () => {
  const InertFunction = FERAL_FUNCTION.prototype.constructor;

  // 9.2.4.1 %ThrowTypeError%

  const argsCalleeDesc = getOwnPropertyDescriptor(makeArguments(), 'callee');
  const ThrowTypeError = argsCalleeDesc && argsCalleeDesc.get;

  // 21.1.5.2 The %StringIteratorPrototype% Object

  // eslint-disable-next-line no-new-wrappers
  const StringIteratorObject = iterateString(new String());
  const StringIteratorPrototype = getPrototypeOf(StringIteratorObject);

  // 21.2.7.1 The %RegExpStringIteratorPrototype% Object
  const RegExpStringIterator =
    regexpPrototype[matchAllSymbol] && matchAllRegExp(/./);
  const RegExpStringIteratorPrototype =
    RegExpStringIterator && getPrototypeOf(RegExpStringIterator);

  // 22.1.5.2 The %ArrayIteratorPrototype% Object

  // eslint-disable-next-line no-array-constructor
  const ArrayIteratorObject = iterateArray([]);
  const ArrayIteratorPrototype = getPrototypeOf(ArrayIteratorObject);

  // 22.2.1 The %TypedArray% Intrinsic Object

  const TypedArray = getPrototypeOf(Float32Array);

  // 23.1.5.2 The %MapIteratorPrototype% Object

  const MapIteratorObject = iterateMap(new Map());
  const MapIteratorPrototype = getPrototypeOf(MapIteratorObject);

  // 23.2.5.2 The %SetIteratorPrototype% Object

  const SetIteratorObject = iterateSet(new Set());
  const SetIteratorPrototype = getPrototypeOf(SetIteratorObject);

  // 25.1.2 The %IteratorPrototype% Object

  const IteratorPrototype = getPrototypeOf(ArrayIteratorPrototype);

  // 25.2.1 The GeneratorFunction Constructor

  // eslint-disable-next-line no-empty-function
  function* GeneratorFunctionInstance() {}
  const GeneratorFunction = getConstructorOf(GeneratorFunctionInstance);

  // 25.2.3 Properties of the GeneratorFunction Prototype Object

  const Generator = GeneratorFunction.prototype;

  // 25.7.1 The AsyncFunction Constructor

  // eslint-disable-next-line no-empty-function
  async function AsyncFunctionInstance() {}
  const AsyncFunction = getConstructorOf(AsyncFunctionInstance);

  const intrinsics = {
    '%InertFunction%': InertFunction,
    '%ArrayIteratorPrototype%': ArrayIteratorPrototype,
    '%InertAsyncFunction%': AsyncFunction,
    '%Generator%': Generator,
    '%InertGeneratorFunction%': GeneratorFunction,
    '%IteratorPrototype%': IteratorPrototype,
    '%MapIteratorPrototype%': MapIteratorPrototype,
    '%RegExpStringIteratorPrototype%': RegExpStringIteratorPrototype,
    '%SetIteratorPrototype%': SetIteratorPrototype,
    '%StringIteratorPrototype%': StringIteratorPrototype,
    '%ThrowTypeError%': ThrowTypeError,
    '%TypedArray%': TypedArray,
    '%InertCompartment%': InertCompartment,
  };

  if (AsyncGeneratorFunctionInstance !== undefined) {
    // 25.3.1 The AsyncGeneratorFunction Constructor

    const AsyncGeneratorFunction = getConstructorOf(
      AsyncGeneratorFunctionInstance,
    );

    // 25.3.2.2 AsyncGeneratorFunction.prototype
    const AsyncGenerator = AsyncGeneratorFunction.prototype;
    // 25.5.1 Properties of the AsyncGenerator Prototype Object
    const AsyncGeneratorPrototype = AsyncGenerator.prototype;
    const AsyncIteratorPrototype = getPrototypeOf(AsyncGeneratorPrototype);

    assign(intrinsics, {
      '%AsyncGenerator%': AsyncGenerator,
      '%InertAsyncGeneratorFunction%': AsyncGeneratorFunction,
      '%AsyncGeneratorPrototype%': AsyncGeneratorPrototype,
      '%AsyncIteratorPrototype%': AsyncIteratorPrototype,
    });
  }

  if (globalThis.Iterator) {
    intrinsics['%IteratorHelperPrototype%'] = getPrototypeOf(
      // eslint-disable-next-line @endo/no-polymorphic-call
      globalThis.Iterator.from([]).take(0),
    );
    intrinsics['%WrapForValidIteratorPrototype%'] = getPrototypeOf(
      // eslint-disable-next-line @endo/no-polymorphic-call
      globalThis.Iterator.from({
        next() {
          return { value: undefined };
        },
      }),
    );
  }

  if (globalThis.AsyncIterator) {
    intrinsics['%AsyncIteratorHelperPrototype%'] = getPrototypeOf(
      // eslint-disable-next-line @endo/no-polymorphic-call
      globalThis.AsyncIterator.from([]).take(0),
    );
    intrinsics['%WrapForValidAsyncIteratorPrototype%'] = getPrototypeOf(
      // eslint-disable-next-line @endo/no-polymorphic-call
      globalThis.AsyncIterator.from({ next() {} }),
    );
  }

  const ab = new ArrayBuffer(0);
  // eslint-disable-next-line @endo/no-polymorphic-call
  const iab = ab.sliceToImmutable();
  const iabProto = getPrototypeOf(iab);
  if (iabProto !== ArrayBuffer.prototype) {
    // In a native implementation, these will be the same prototype
    intrinsics['%ImmutableArrayBufferPrototype%'] = iabProto;
  }

  return intrinsics;
};$h͏_once.getAnonymousIntrinsics(getAnonymousIntrinsics);
})()
,
// === 52. ses ./src/tame-harden.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let freeze;$h͏_imports([["./commons.js", [["freeze",[$h͏_a => (freeze = $h͏_a)]]]]]);


/** @import {Harden} from '../types.js'; */

/** @type {(safeHarden: Harden, hardenTaming: 'safe' | 'unsafe') => Harden} */
       const tameHarden = (safeHarden, hardenTaming) => {
  if (hardenTaming === 'safe') {
    return safeHarden;
  }

  // In on the joke
  Object.isExtensible = () => false;
  Object.isFrozen = () => true;
  Object.isSealed = () => true;
  Reflect.isExtensible = () => false;

  // @ts-expect-error secret property
  if (safeHarden.isFake) {
    // The "safe" hardener is already a fake hardener.
    // Just use it.
    return safeHarden;
  }

  const fakeHarden = arg => arg;
  fakeHarden.isFake = true;
  return freeze(fakeHarden);
};$h͏_once.tameHarden(tameHarden);
freeze(tameHarden);
})()
,
// === 53. ses ./src/tame-symbol-constructor.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let Symbol,entries,fromEntries,getOwnPropertyDescriptors,defineProperties,arrayMap,functionBind;$h͏_imports([["./commons.js", [["Symbol",[$h͏_a => (Symbol = $h͏_a)]],["entries",[$h͏_a => (entries = $h͏_a)]],["fromEntries",[$h͏_a => (fromEntries = $h͏_a)]],["getOwnPropertyDescriptors",[$h͏_a => (getOwnPropertyDescriptors = $h͏_a)]],["defineProperties",[$h͏_a => (defineProperties = $h͏_a)]],["arrayMap",[$h͏_a => (arrayMap = $h͏_a)]],["functionBind",[$h͏_a => (functionBind = $h͏_a)]]]]]);









/**
 * This taming provides a tamed alternative to the original `Symbol` constructor
 * that starts off identical, except that all its properties are "temporarily"
 * configurable. The original `Symbol` constructor remains unmodified on
 * the start compartment's global. The tamed alternative is used as the shared
 * `Symbol` constructor on constructed compartments.
 *
 * Starting these properties as configurable assumes two succeeding phases of
 * processing: A permit enforcement phase, that
 * removes all properties not on the permits (which requires them to be
 * configurable) and a global hardening step that freezes all primordials,
 * returning these properties to their expected non-configurable status.
 *
 * The ses shim is constructed to eventually enable vetted shims to run between
 * repair and global hardening. However, such vetted shims would normally
 * run in the start compartment, which continues to use the original unmodified
 * `Symbol`, so they should not normally be affected by the temporary
 * configurability of these properties.
 *
 * Note that the spec refers to the global `Symbol` function as the
 * ["Symbol Constructor"](https://tc39.es/ecma262/multipage/fundamental-objects.html#sec-symbol-constructor)
 * even though it has a call behavior (can be called as a function) and does not
 * not have a construct behavior (cannot be called with `new`). Accordingly,
 * to tame it, we must replace it with a function without a construct
 * behavior.
 */
       const tameSymbolConstructor = () => {
  const OriginalSymbol = Symbol;
  const SymbolPrototype = OriginalSymbol.prototype;

  // Bypass Hermes bug, fixed in: https://github.com/facebook/hermes/commit/00f18c89c720e1c34592bb85a1a8d311e6e99599
  // Make a "copy" of the primordial [Symbol "constructor"](https://tc39.es/ecma262/#sec-symbol-description) which maintains all observable behavior. The primordial explicitly throws on `[[Construct]]` and has a `[[Call]]` which ignores the receiver. Binding also maintains the `toString` source as a native function. The `name` is restored below when copying own properties.
  const SharedSymbol = functionBind(Symbol, undefined);

  defineProperties(SymbolPrototype, {
    constructor: {
      value: SharedSymbol
      // leave other `constructor` attributes as is
    },
  });

  const originalDescsEntries = entries(
    getOwnPropertyDescriptors(OriginalSymbol),
  );
  const descs = fromEntries(
    arrayMap(originalDescsEntries, ([name, desc]) => [
      name,
      { ...desc, configurable: true },
    ]),
  );
  defineProperties(SharedSymbol, descs);

  return { '%SharedSymbol%': SharedSymbol };
};$h͏_once.tameSymbolConstructor(tameSymbolConstructor);
})()
,
// === 54. ses ./src/tame-faux-data-properties.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let getOwnPropertyDescriptor,apply,defineProperty,toStringTagSymbol;$h͏_imports([["./commons.js", [["getOwnPropertyDescriptor",[$h͏_a => (getOwnPropertyDescriptor = $h͏_a)]],["apply",[$h͏_a => (apply = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["toStringTagSymbol",[$h͏_a => (toStringTagSymbol = $h͏_a)]]]]]);






const throws = thunk => {
  try {
    thunk();
    return false;
  } catch (er) {
    return true;
  }
};

/**
 * Exported for convenience of unit testing. Harmless, but not expected
 * to be useful by itself.
 *
 * @param {any} obj
 * @param {string|symbol} prop
 * @param {any} expectedValue
 * @returns {boolean}
 * Returns whether `tameFauxDataProperty` turned the property in question
 * from an apparent faux data property into the actual data property it
 * seemed to emulate.
 * If this function returns `false`, then we hope no effects happened.
 * However, sniffing out if an accessor property seems to be a faux data
 * property requires invoking the getter and setter functions that might
 * possibly have side effects.
 * `tameFauxDataProperty` is not in a position to tell.
 */
       const tameFauxDataProperty = (obj, prop, expectedValue) => {
  if (obj === undefined) {
    // The object does not exist in this version of the platform
    return false;
  }
  const desc = getOwnPropertyDescriptor(obj, prop);
  if (!desc || 'value' in desc) {
    // The property either doesn't exist, or is already an actual data property.
    return false;
  }
  const { get, set } = desc;
  if (typeof get !== 'function' || typeof set !== 'function') {
    // A faux data property has both a getter and a setter
    return false;
  }
  if (get() !== expectedValue) {
    // The getter called by itself should produce the expectedValue
    return false;
  }
  if (apply(get, obj, []) !== expectedValue) {
    // The getter called with `this === obj` should also return the
    // expectedValue.
    return false;
  }
  const testValue = 'Seems to be a setter';
  const subject1 = { __proto__: null };
  apply(set, subject1, [testValue]);
  if (subject1[prop] !== testValue) {
    // The setter called with an unrelated object as `this` should
    // set the property on the object.
    return false;
  }
  const subject2 = { __proto__: obj };
  apply(set, subject2, [testValue]);
  if (subject2[prop] !== testValue) {
    // The setter called on an object that inherits from `obj` should
    // override the property from `obj` as if by assignment.
    return false;
  }
  if (!throws(() => apply(set, obj, [expectedValue]))) {
    // The setter called with `this === obj` should throw without having
    // caused any effect.
    // This is the test that has the greatest danger of leaving behind some
    // persistent side effect. The most obvious one is to emulate a
    // successful assignment to the property. That's why this test
    // uses `expectedValue`, so that case is likely not to actually
    // change anything.
    return false;
  }
  if ('originalValue' in get) {
    // The ses-shim uniquely, as far as we know, puts an `originalValue`
    // property on the getter, so that reflect property tranversal algorithms,
    // like `harden`, will traverse into the enulated value without
    // calling the getter. That does not happen until `permits-intrinsics.js`
    // which is much later. So if we see one this early, we should
    // not assume we understand what's going on.
    return false;
  }

  // We assume that this code runs before any untrusted code runs, so
  // we do not need to worry about the above conditions passing because of
  // malicious intent. In fact, it runs even before vetted shims are supposed
  // to run, between repair and hardening. Given that, after all these tests
  // pass, we have adequately validated that the property in question is
  // an accessor function whose purpose is suppressing the override mistake,
  // i.e., enabling a non-writable property to be overridden by assignment.
  // In that case, here we *temporarily* turn it into the data property
  // it seems to emulate, but writable so that it does not trigger the
  // override mistake while in this temporary state.

  // For those properties that are also listed in `enablements.js`,
  // that phase will re-enable override for these properties, but
  // via accessor functions that SES controls, so we know what they are
  // doing. In addition, the getter functions installed by
  // `enable-property-overrides.js` have an `originalValue` field
  // enabling meta-traversal code like harden to visit the original value
  // without calling the getter.

  if (desc.configurable === false) {
    // Even though it seems to be a faux data property, we're unable to fix it.
    return false;
  }

  // Many of the `return false;` cases above plausibly should be turned into
  // errors, or an least generate warnings. However, for those, the checks
  // following this phase are likely to signal an error anyway.

  // At this point, we have passed all our sniff checks for validating that
  // it seems to be a faux data property with the expected value. Turn
  // it into the actual data property it emulates, but writable so there is
  // not yet an override mistake problem.

  defineProperty(obj, prop, {
    value: expectedValue,
    writable: true,
    enumerable: desc.enumerable,
    configurable: true,
  });

  return true;
};

/**
 * In JavaScript, the so-called "override mistake" is the inability to
 * override an inherited non-writable data property by assignment. A common
 * workaround is to instead define an accessor property that acts like
 * a non-writable data property, except that it allows an object that
 * inherits this property to override it by assignment. Let's call
 * an access property that acts this way a "faux data property". In this
 * ses-shim, `enable-property-overrides.js` makes the properties listed in
 * `enablements.js` into faux data properties.
 *
 * But the ses-shim is not alone in use of this trick. Starting with the
 * [Iterator Helpers proposal](https://github.com/tc39/proposal-iterator-helpers),
 * some properties are defined as (what we call) faux data properties.
 * Some of these are new properties (`Interator.prototype.constructor`) and
 * some are old data properties converted to accessor properties
 * (`Iterator.prototype[String.toStringTag]`). So the ses-shim needs to be
 * prepared for some enumerated set of properties to already be faux data
 * properties in the platform prior to our initialization.
 *
 * For these possible faux data properties, it is important that
 * `permits.js` describe each as a data property, so that it can further
 * constrain the apparent value (that allegedly would be returned by the
 * getter) according to its own permits.
 *
 * However, at the time of this writing, the precise behavior specified
 * by the iterator-helpers proposal for these faux data properties is
 * novel. We should not be too confident that all further such platform
 * additions do what we would now expect. So, for each of these possible
 * faux data properties, we do some sniffing to see if it behaves as we
 * currently expect a faux data property to act. If not, then
 * `tameFauxDataProperties` tries not to modify it, leaving it to later
 * checks, especially `permits-intrinsics.js`, to error when it sees an
 * unexpected accessor.
 *
 * If one of these enumerated accessor properties does seem to be
 * a faithful faux data property, then `tameFauxDataProperties` itself
 * *tempoarily* turns it into the actual data property that it seems to emulate.
 * This data property starts as writable, so that in this state it will
 * not trigger the override mistake, i.e., assignment to an object inheriting
 * this property is allowed to succeed at overriding this property.
 *
 * For those properties that should be a faux data property rather than an
 * actual one, such as those from the iterator-helpers proposal,
 * they should be listed as such in `enablements.js`, so
 * `enable-property-overrides.js` will turn it back into a faux data property.
 * But one controlled by the ses-shim, whose behavior we understand.
 *
 * `tameFauxDataProperties`, which turns these into actual data properties,
 * happens during the `repairIntrinsics` phase
 * of `lockdown`, before even vetted shim are supposed to run.
 * `enable-property-overrides.js` runs after vetted shims, turning the
 * appropriate ones back into faux data properties. Thus vetted shims
 * can observe the possibly non-conforming state where these are temporarily
 * actual data properties, rather than faux data properties.
 *
 * Coordinate the property enumeration here
 * with `enablements.js`, so the appropriate properties are
 * turned back to faux data properties.
 *
 * @param {Record<any,any>} intrinsics
 */$h͏_once.tameFauxDataProperty(tameFauxDataProperty);
       const tameFauxDataProperties = intrinsics => {
  // https://github.com/tc39/proposal-iterator-helpers
  tameFauxDataProperty(
    intrinsics['%IteratorPrototype%'],
    'constructor',
    intrinsics.Iterator,
  );
  // https://github.com/tc39/proposal-iterator-helpers
  tameFauxDataProperty(
    intrinsics['%IteratorPrototype%'],
    toStringTagSymbol,
    'Iterator',
  );
};$h͏_once.tameFauxDataProperties(tameFauxDataProperties);
})()
,
// === 55. ses ./src/tame-regenerator-runtime.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let defineProperty,iteratorPrototype,iteratorSymbol,hasOwn;$h͏_imports([["./commons.js", [["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]],["iteratorPrototype",[$h͏_a => (iteratorPrototype = $h͏_a)]],["iteratorSymbol",[$h͏_a => (iteratorSymbol = $h͏_a)]],["hasOwn",[$h͏_a => (hasOwn = $h͏_a)]]]]]);






       const tameRegeneratorRuntime = () => {
  const iter = iteratorPrototype[iteratorSymbol];
  defineProperty(iteratorPrototype, iteratorSymbol, {
    configurable: true,
    get() {
      return iter;
    },
    set(value) {
      // ignore the assignment on IteratorPrototype
      if (this === iteratorPrototype) return;
      if (hasOwn(this, iteratorSymbol)) {
        this[iteratorSymbol] = value;
      }
      defineProperty(this, iteratorSymbol, {
        value,
        writable: true,
        enumerable: true,
        configurable: true,
      });
    },
  });
};$h͏_once.tameRegeneratorRuntime(tameRegeneratorRuntime);
})()
,
// === 56. ses ./src/shim-arraybuffer-transfer.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let ArrayBuffer,arrayBufferPrototype,arrayBufferSlice,arrayBufferGetByteLength,Uint8Array,typedArraySet,globalThis,TypeError,defineProperty;$h͏_imports([["./commons.js", [["ArrayBuffer",[$h͏_a => (ArrayBuffer = $h͏_a)]],["arrayBufferPrototype",[$h͏_a => (arrayBufferPrototype = $h͏_a)]],["arrayBufferSlice",[$h͏_a => (arrayBufferSlice = $h͏_a)]],["arrayBufferGetByteLength",[$h͏_a => (arrayBufferGetByteLength = $h͏_a)]],["Uint8Array",[$h͏_a => (Uint8Array = $h͏_a)]],["typedArraySet",[$h͏_a => (typedArraySet = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["defineProperty",[$h͏_a => (defineProperty = $h͏_a)]]]]]);











       const shimArrayBufferTransfer = () => {
  if (typeof arrayBufferPrototype.transfer === 'function') {
    // Assume already exists so does not need to be shimmed.
    // Such conditional shimming is ok in this case since ArrayBuffer.p.transfer
    // is already officially part of JS.
    //
    // Empty object because this shim has nothing for `addIntrinsics` to add.
    return {};
  }
  const clone = globalThis.structuredClone;
  if (typeof clone !== 'function') {
    // On a platform with neither `Array.prototype.transfer`
    // nor `structuredClone`, this shim does nothing.
    // For example, Node <= 16 has neither.
    //
    // Empty object because this shim has nothing for `addIntrinsics` to add.
    return {};
    // TODO Rather than doing nothing, should the endo ses-shim throw
    // in this case?
    // throw TypeError(
    //   `Can only shim missing ArrayBuffer.prototype.transfer on a platform with "structuredClone"`,
    // );
    // For example, endo no longer supports Node <= 16. All browsers have
    // `structuredClone`. XS has `Array.prototype.transfer`. Are there still
    // any platforms without both that Endo should still support?
    // What about Hermes?
  }

  /**
   * @type {ThisType<ArrayBuffer>}
   */
  const methods = {
    /**
     * @param {number} [newLength]
     */
    transfer(newLength = undefined) {
      // Using this builtin getter also ensures that `this` is a genuine
      // ArrayBuffer.
      const oldLength = arrayBufferGetByteLength(this);
      if (newLength === undefined || newLength === oldLength) {
        return clone(this, { transfer: [this] });
      }
      if (typeof newLength !== 'number') {
        throw TypeError(`transfer newLength if provided must be a number`);
      }
      if (newLength > oldLength) {
        const result = new ArrayBuffer(newLength);
        const taOld = new Uint8Array(this);
        const taNew = new Uint8Array(result);
        typedArraySet(taNew, taOld);
        // Using clone only to detach, and only after the copy succeeds
        clone(this, { transfer: [this] });
        return result;
      } else {
        const result = arrayBufferSlice(this, 0, newLength);
        // Using clone only to detach, and only after the slice succeeds
        clone(this, { transfer: [this] });
        return result;
      }
    },
  };

  defineProperty(arrayBufferPrototype, 'transfer', {
    // @ts-expect-error
    value: methods.transfer,
    writable: true,
    enumerable: false,
    configurable: true,
  });

  // Empty object because this shim has nothing for `addIntrinsics` to add.
  return {};
};$h͏_once.shimArrayBufferTransfer(shimArrayBufferTransfer);
})()
,
// === 57. ses ./src/reporting.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let globalThis,assert;$h͏_imports([["./commons.js", [["globalThis",[$h͏_a => (globalThis = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]]]]]);


/**
 * @import {Reporter, GroupReporter} from './reporting-types.js'
 */

/* eslint-disable @endo/no-polymorphic-call */
/**
 * To address https://github.com/endojs/endo/issues/2908,
 * the `consoleReporter` uses the current `console` rather
 * than the original one.
 *
 * @type {GroupReporter}
 */
const consoleReporter = {
  warn(...args) {
    globalThis.console.warn(...args);
  },
  error(...args) {
    globalThis.console.error(...args);
  },
  ...(globalThis.console?.groupCollapsed
    ? {
        groupCollapsed(...args) {
          globalThis.console.groupCollapsed(...args);
        },
      }
    : undefined),
  ...(globalThis.console?.groupEnd
    ? {
        groupEnd() {
          globalThis.console.groupEnd();
        },
      }
    : undefined),
};
/* eslint-enable @endo/no-polymorphic-call */

/**
 * Creates a suitable reporter for internal errors and warnings out of the
 * Node.js console.error to ensure all messages go to stderr, including the
 * group label.
 * Accounts for the extra space introduced by console.error as a delimiter
 * between the indent and subsequent arguments.
 *
 * @param {(...message: Array<any>) => void} print
 */
const makeReportPrinter = print => {
  let indent = false;
  /** @param {Array<any>} args */
  const printIndent = (...args) => {
    if (indent) {
      print(' ', ...args);
    } else {
      print(...args);
    }
  };
  return /** @type {GroupReporter} */ ({
    warn(...args) {
      printIndent(...args);
    },
    error(...args) {
      printIndent(...args);
    },
    groupCollapsed(...args) {
      assert(!indent);
      print(...args);
      indent = true;
    },
    groupEnd() {
      indent = false;
    },
  });
};

const mute = () => {};

/**
 * @param {"platform" | "console" | "none"} reporting
 */
       const chooseReporter = reporting => {
  if (reporting === 'none') {
    return makeReportPrinter(mute);
  }
  if (globalThis.console !== undefined) {
    if (
      reporting === 'console' || // asks for console explicitly
      globalThis.window === globalThis || // likely on browser
      globalThis.importScripts !== undefined // likely on worker
    ) {
      // reporter just delegates directly to the current console
      return consoleReporter;
    }
    assert(reporting === 'platform');
    // On Node.js, we send all feedback to stderr, regardless of purported level.
    // This uses `consoleReporter.error` instead of `console.error` because we
    // want the constructed reporter to use the `console.error` of the current
    // `console`, not the `console` that was installed when the reporter
    // was created.
    return makeReportPrinter(consoleReporter.error);
  }
  if (globalThis.print !== undefined) {
    return makeReportPrinter(globalThis.print);
  }
  return makeReportPrinter(mute);
};

/**
 * @param {string} groupLabel
 * @param {GroupReporter} console
 * @param {(internalConsole: Reporter) => void} callback
 */$h͏_once.chooseReporter(chooseReporter);
       const reportInGroup = (groupLabel, console, callback) => {
  const { warn, error, groupCollapsed, groupEnd } = console;
  const grouping = groupCollapsed && groupEnd;
  let groupStarted = false;
  try {
    return callback({
      warn(...args) {
        if (grouping && !groupStarted) {
          groupCollapsed(groupLabel);
          groupStarted = true;
        }
        warn(...args);
      },
      error(...args) {
        if (grouping && !groupStarted) {
          groupCollapsed(groupLabel);
          groupStarted = true;
        }
        error(...args);
      },
    });
  } finally {
    if (grouping && groupStarted) {
      groupEnd();
      groupStarted = false;
    }
  }
};$h͏_once.reportInGroup(reportInGroup);
})()
,
// === 58. ses ./src/lockdown.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let getenv,FERAL_FUNCTION,FERAL_EVAL,TypeError,arrayFilter,globalThis,is,ownKeys,stringSplit,symbolFor,noEvalEvaluate,getOwnPropertyNames,getPrototypeOf,makeHardener,makeIntrinsicsCollector,removeUnpermittedIntrinsics,tameFunctionConstructors,tameDateConstructor,tameMathObject,tameRegExpConstructor,enablePropertyOverrides,tameLocaleMethods,setGlobalObjectConstantProperties,setGlobalObjectMutableProperties,setGlobalObjectEvaluators,makeSafeEvaluator,initialGlobalPropertyNames,tameFunctionToString,tameDomains,tameModuleSource,tameConsole,tameErrorConstructor,assert,makeAssert,getAnonymousIntrinsics,makeCompartmentConstructor,tameHarden,tameSymbolConstructor,tameFauxDataProperties,tameRegeneratorRuntime,shimArrayBufferTransfer,reportInGroup,chooseReporter;$h͏_imports([["@endo/env-options", [["getEnvironmentOption",[$h͏_a => (getenv = $h͏_a)]]]],["@endo/immutable-arraybuffer/shim.js", []],["./commons.js", [["FERAL_FUNCTION",[$h͏_a => (FERAL_FUNCTION = $h͏_a)]],["FERAL_EVAL",[$h͏_a => (FERAL_EVAL = $h͏_a)]],["TypeError",[$h͏_a => (TypeError = $h͏_a)]],["arrayFilter",[$h͏_a => (arrayFilter = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]],["is",[$h͏_a => (is = $h͏_a)]],["ownKeys",[$h͏_a => (ownKeys = $h͏_a)]],["stringSplit",[$h͏_a => (stringSplit = $h͏_a)]],["symbolFor",[$h͏_a => (symbolFor = $h͏_a)]],["noEvalEvaluate",[$h͏_a => (noEvalEvaluate = $h͏_a)]],["getOwnPropertyNames",[$h͏_a => (getOwnPropertyNames = $h͏_a)]],["getPrototypeOf",[$h͏_a => (getPrototypeOf = $h͏_a)]]]],["./make-hardener.js", [["makeHardener",[$h͏_a => (makeHardener = $h͏_a)]]]],["./intrinsics.js", [["makeIntrinsicsCollector",[$h͏_a => (makeIntrinsicsCollector = $h͏_a)]]]],["./permits-intrinsics.js", [["default",[$h͏_a => (removeUnpermittedIntrinsics = $h͏_a)]]]],["./tame-function-constructors.js", [["default",[$h͏_a => (tameFunctionConstructors = $h͏_a)]]]],["./tame-date-constructor.js", [["default",[$h͏_a => (tameDateConstructor = $h͏_a)]]]],["./tame-math-object.js", [["default",[$h͏_a => (tameMathObject = $h͏_a)]]]],["./tame-regexp-constructor.js", [["default",[$h͏_a => (tameRegExpConstructor = $h͏_a)]]]],["./enable-property-overrides.js", [["default",[$h͏_a => (enablePropertyOverrides = $h͏_a)]]]],["./tame-locale-methods.js", [["default",[$h͏_a => (tameLocaleMethods = $h͏_a)]]]],["./global-object.js", [["setGlobalObjectConstantProperties",[$h͏_a => (setGlobalObjectConstantProperties = $h͏_a)]],["setGlobalObjectMutableProperties",[$h͏_a => (setGlobalObjectMutableProperties = $h͏_a)]],["setGlobalObjectEvaluators",[$h͏_a => (setGlobalObjectEvaluators = $h͏_a)]]]],["./make-safe-evaluator.js", [["makeSafeEvaluator",[$h͏_a => (makeSafeEvaluator = $h͏_a)]]]],["./permits.js", [["initialGlobalPropertyNames",[$h͏_a => (initialGlobalPropertyNames = $h͏_a)]]]],["./tame-function-tostring.js", [["tameFunctionToString",[$h͏_a => (tameFunctionToString = $h͏_a)]]]],["./tame-domains.js", [["tameDomains",[$h͏_a => (tameDomains = $h͏_a)]]]],["./tame-module-source.js", [["tameModuleSource",[$h͏_a => (tameModuleSource = $h͏_a)]]]],["./error/tame-console.js", [["tameConsole",[$h͏_a => (tameConsole = $h͏_a)]]]],["./error/tame-error-constructor.js", [["default",[$h͏_a => (tameErrorConstructor = $h͏_a)]]]],["./error/assert.js", [["assert",[$h͏_a => (assert = $h͏_a)]],["makeAssert",[$h͏_a => (makeAssert = $h͏_a)]]]],["./get-anonymous-intrinsics.js", [["getAnonymousIntrinsics",[$h͏_a => (getAnonymousIntrinsics = $h͏_a)]]]],["./compartment.js", [["makeCompartmentConstructor",[$h͏_a => (makeCompartmentConstructor = $h͏_a)]]]],["./tame-harden.js", [["tameHarden",[$h͏_a => (tameHarden = $h͏_a)]]]],["./tame-symbol-constructor.js", [["tameSymbolConstructor",[$h͏_a => (tameSymbolConstructor = $h͏_a)]]]],["./tame-faux-data-properties.js", [["tameFauxDataProperties",[$h͏_a => (tameFauxDataProperties = $h͏_a)]]]],["./tame-regenerator-runtime.js", [["tameRegeneratorRuntime",[$h͏_a => (tameRegeneratorRuntime = $h͏_a)]]]],["./shim-arraybuffer-transfer.js", [["shimArrayBufferTransfer",[$h͏_a => (shimArrayBufferTransfer = $h͏_a)]]]],["./reporting.js", [["reportInGroup",[$h͏_a => (reportInGroup = $h͏_a)]],["chooseReporter",[$h͏_a => (chooseReporter = $h͏_a)]]]]]);































































/** @import {LockdownOptions} from '../types.js' */

const { Fail, details: X, quote: q } = assert;

/** @type {Error=} */
let priorRepairIntrinsics;

/** @type {Error=} */
let priorHardenIntrinsics;

// Build a harden() with an empty fringe.
// Gate it on lockdown.
/**
 * @template T
 * @param {T} ref
 * @returns {T}
 */
const safeHarden = makeHardener();

/**
 * @callback Transform
 * @param {string} source
 * @returns {string}
 */

/**
 * @callback CompartmentConstructor
 * @param {object} endowments
 * @param {object} moduleMap
 * @param {object} [options]
 * @param {Array<Transform>} [options.transforms]
 * @param {Array<Transform>} [options.__shimTransforms__]
 */

// TODO https://github.com/endojs/endo/issues/814
// Lockdown currently allows multiple calls provided that the specified options
// of every call agree.  With experience, we have observed that lockdown should
// only ever need to be called once and that simplifying lockdown will improve
// the quality of audits.

const probeHostEvaluators = () => {
  let functionAllowed;
  try {
    functionAllowed = FERAL_FUNCTION('return true')();
  } catch (_error) {
    // We reach here if the Function() constructor is outright forbidden by a
    // strict Content Security Policy (containing either a `default-src` or a
    // `script-src` directive), not been implemented in the host, or the host
    // is configured to throw an exception instead of `new Function`.
    functionAllowed = false;
  }

  let evalAllowed;
  try {
    evalAllowed = FERAL_EVAL('true');
  } catch (_error) {
    // We reach here if `eval` is outright forbidden by a strict Content Security Policy,
    // not implemented in the host, or the host is configured to throw an exception.
    // We allow this for SES usage that delegates the responsibility to isolate
    // guest code to production code generation.
    evalAllowed = false;
  }

  let directEvalAllowed;
  if (functionAllowed && evalAllowed) {
    directEvalAllowed = FERAL_FUNCTION(
      'eval',
      'SES_changed',
      `\
        eval("SES_changed = true");
        return SES_changed;
      `,
    )(FERAL_EVAL, false);
    // If we get here and SES_changed stayed false, that means the eval was sloppy
    // and indirect, which generally creates a new global.
    // We are going to throw an exception for failing to initialize SES, but
    // good neighbors clean up.
    if (!directEvalAllowed) {
      delete globalThis.SES_changed;
    }
  }

  return { functionAllowed, evalAllowed, directEvalAllowed };
};

/**
 * @param {LockdownOptions} [options]
 */
       const repairIntrinsics = (options = {}) => {
  // First time, absent options default to 'safe'.
  // Subsequent times, absent options default to first options.
  // Thus, all present options must agree with first options.
  // Reconstructing `option` here also ensures that it is a well
  // behaved record, with only own data properties.
  //
  // The `overrideTaming` is not a safety issue. Rather it is a tradeoff
  // between code compatibility, which is better with the `'moderate'`
  // setting, and tool compatibility, which is better with the `'min'`
  // setting. See
  // https://github.com/Agoric/SES-shim/blob/master/packages/ses/README.md#enabling-override-by-assignment)
  // for an explanation of when to use which.
  //
  // The `stackFiltering` is not a safety issue. Rather it is a tradeoff
  // between relevance and completeness of the stack frames shown on the
  // console. Setting`stackFiltering` to `'verbose'` applies no filters, providing
  // the raw stack frames that can be quite verbose. Setting
  // `stackFrameFiltering` to`'concise'` limits the display to the stack frame
  // information most likely to be relevant, eliminating distracting frames
  // such as those from the infrastructure. However, the bug you're trying to
  // track down might be in the infrastructure, in which case the `'verbose'` setting
  // is useful. See
  // [`stackFiltering` options](https://github.com/Agoric/SES-shim/blob/master/packages/ses/docs/lockdown.md#stackfiltering-options)
  // for an explanation.

  const {
    errorTaming = /** @type {'safe' | 'unsafe' | 'unsafe-debug'} */ (
      getenv('LOCKDOWN_ERROR_TAMING', 'safe', ['unsafe', 'unsafe-debug'])
    ),
    errorTrapping = /** @type {'platform' | 'none' | 'report' | 'abort' | 'exit'} */ (
      getenv('LOCKDOWN_ERROR_TRAPPING', 'platform', [
        'none',
        'report',
        'abort',
        'exit',
      ])
    ),
    reporting = /** @type {'platform' | 'console' | 'none'} */ (
      getenv('LOCKDOWN_REPORTING', 'platform', ['console', 'none'])
    ),
    unhandledRejectionTrapping = /** @type {'none' | 'report'} */ (
      getenv('LOCKDOWN_UNHANDLED_REJECTION_TRAPPING', 'report', ['none'])
    ),
    regExpTaming = /** @type {'safe' | 'unsafe'} */ (
      getenv('LOCKDOWN_REGEXP_TAMING', 'safe', ['unsafe'])
    ),
    localeTaming = /** @type {'safe' | 'unsafe'} */ (
      getenv('LOCKDOWN_LOCALE_TAMING', 'safe', ['unsafe'])
    ),
    consoleTaming = /** @type {'unsafe' | 'safe'} */ (
      getenv('LOCKDOWN_CONSOLE_TAMING', 'safe', ['unsafe'])
    ),
    overrideTaming = /** @type {'moderate' | 'min' | 'severe'} */ (
      getenv('LOCKDOWN_OVERRIDE_TAMING', 'moderate', ['min', 'severe'])
    ),
    stackFiltering = /** @type {'concise' | 'omit-frames' | 'shorten-paths' | 'verbose'} */ (
      getenv('LOCKDOWN_STACK_FILTERING', 'concise', [
        'omit-frames',
        'shorten-paths',
        'verbose',
      ])
    ),
    domainTaming = /** @type {'safe' | 'unsafe'} */ (
      getenv('LOCKDOWN_DOMAIN_TAMING', 'safe', ['unsafe'])
    ),
    evalTaming = /** @type {'safe-eval' | 'unsafe-eval' | 'no-eval'} */ (
      getenv('LOCKDOWN_EVAL_TAMING', 'safe-eval', [
        'unsafe-eval',
        'no-eval',
        // deprecated
        'safeEval',
        'unsafeEval',
        'noEval',
      ])
    ),
    overrideDebug = /** @type {string[]} */ (
      arrayFilter(
        stringSplit(getenv('LOCKDOWN_OVERRIDE_DEBUG', ''), ','),
        /** @param {string} debugName */
        debugName => debugName !== '',
      )
    ),
    legacyRegeneratorRuntimeTaming = /** @type {'safe' | 'unsafe-ignore'} */ (
      getenv('LOCKDOWN_LEGACY_REGENERATOR_RUNTIME_TAMING', 'safe', [
        'unsafe-ignore',
      ])
    ),
    __hardenTaming__ = /** @type {'safe' | 'unsafe'} */ (
      getenv('LOCKDOWN_HARDEN_TAMING', 'safe', ['unsafe'])
    ),
    dateTaming, // deprecated
    mathTaming, // deprecated
    ...extraOptions
  } = options;

  // Assert that only supported options were passed.
  // Use Reflect.ownKeys to reject symbol-named properties as well.
  const extraOptionsNames = ownKeys(extraOptions);
  extraOptionsNames.length === 0 ||
    Fail`lockdown(): non supported option ${q(extraOptionsNames)}`;

  const reporter = chooseReporter(reporting);
  const { warn } = reporter;

  if (dateTaming !== undefined) {
    warn(
      `SES The 'dateTaming' option is deprecated and does nothing. In the future specifying it will be an error.`,
    );
  }
  if (mathTaming !== undefined) {
    warn(
      `SES The 'mathTaming' option is deprecated and does nothing. In the future specifying it will be an error.`,
    );
  }

  priorRepairIntrinsics === undefined ||
    // eslint-disable-next-line @endo/no-polymorphic-call
    assert.fail(
      X`Already locked down at ${priorRepairIntrinsics} (SES_ALREADY_LOCKED_DOWN)`,
      TypeError,
    );
  // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_ALREADY_LOCKED_DOWN.md
  priorRepairIntrinsics = TypeError('Prior lockdown (SES_ALREADY_LOCKED_DOWN)');
  // Tease V8 to generate the stack string and release the closures the stack
  // trace retained:
  priorRepairIntrinsics.stack;

  const { functionAllowed, evalAllowed, directEvalAllowed } =
    probeHostEvaluators();

  if (
    directEvalAllowed === false &&
    evalTaming === 'safe-eval' &&
    (functionAllowed || evalAllowed)
  ) {
    // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_DIRECT_EVAL.md
    throw TypeError(
      "SES cannot initialize unless 'eval' is the original intrinsic 'eval', suitable for direct eval (dynamically scoped eval) (SES_DIRECT_EVAL)",
    );
  }

  /**
   * Because of packagers and bundlers, etc, multiple invocations of lockdown
   * might happen in separate instantiations of the source of this module.
   * In that case, each one sees its own `firstOptions` variable, so the test
   * above will not detect that lockdown has already happened. We
   * unreliably test some telltale signs that lockdown has run, to avoid
   * trying to lock down a locked down environment. Although the test is
   * unreliable, this is consistent with the SES threat model. SES provides
   * security only if it runs first in a given realm, or if everything that
   * runs before it is SES-aware and cooperative. Neither SES nor anything
   * can protect itself from corrupting code that runs first. For these
   * purposes, code that turns a realm into something that passes these
   * tests without actually locking down counts as corrupting code.
   *
   * The specifics of what this tests for may change over time, but it
   * should be consistent with any setting of the lockdown options.
   */
  const seemsToBeLockedDown = () => {
    return (
      globalThis.Function.prototype.constructor !== globalThis.Function &&
      // @ts-ignore harden is absent on globalThis type def.
      typeof globalThis.harden === 'function' &&
      // @ts-ignore lockdown is absent on globalThis type def.
      typeof globalThis.lockdown === 'function' &&
      globalThis.Date.prototype.constructor !== globalThis.Date &&
      typeof globalThis.Date.now === 'function' &&
      // @ts-ignore does not recognize that Date constructor is a special
      // Function.
      // eslint-disable-next-line @endo/no-polymorphic-call
      is(globalThis.Date.prototype.constructor.now(), NaN)
    );
  };

  if (seemsToBeLockedDown()) {
    // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_MULTIPLE_INSTANCES.md
    throw TypeError(
      `Already locked down but not by this SES instance (SES_MULTIPLE_INSTANCES)`,
    );
  }

  /**
   * 1. TAME powers & gather intrinsics first.
   */

  tameDomains(domainTaming);

  // Replace Function.prototype.toString with one that recognizes
  // shimmed functions as honorary native functions.
  const markVirtualizedNativeFunction = tameFunctionToString();

  const { addIntrinsics, completePrototypes, finalIntrinsics } =
    makeIntrinsicsCollector(reporter);

  const tamedHarden = tameHarden(safeHarden, __hardenTaming__);
  addIntrinsics({ harden: tamedHarden });

  addIntrinsics(tameFunctionConstructors());

  addIntrinsics(tameDateConstructor());
  addIntrinsics(tameErrorConstructor(errorTaming, stackFiltering));
  addIntrinsics(tameMathObject());
  addIntrinsics(tameRegExpConstructor(regExpTaming));
  addIntrinsics(tameSymbolConstructor());
  addIntrinsics(shimArrayBufferTransfer());
  addIntrinsics(tameModuleSource());

  addIntrinsics(getAnonymousIntrinsics());

  completePrototypes();

  const intrinsics = finalIntrinsics();

  // Install Object[@harden] or abort.
  const symbolForHarden = symbolFor('harden');
  const priorHarden = intrinsics.Object[symbolForHarden];
  if (priorHarden) {
    // By convention, if a module like @endo/harden gets used before lockdown,
    // it will install itself as a non-configurable, non-writable property over
    // Object[@harden] so that versions of SES predating the introduction of
    // Object[@harden] will fail to lockdown because they cannot remove an
    // unknown intrinsic.
    // All newer versions explicitly check for Object[@harden] (here).
    // The @endo/harden implementation additionally captures a stack trace
    // where harden was first used to assist developers in tracking down the
    // hardened module that was initialized before lockdown.
    if (priorHarden.lockdownError) {
      throw priorHarden.lockdownError;
    }
    // And in the event a library installs Object[@harden] without leaving a
    // hint, we fall back to a generic lockdown error.
    throw new TypeError(
      'Cannot lockdown (repairIntrinsics) if a prior harden implementation has been used and installed. Check for libraries using @endo/harden before lockdown.',
    );
  }
  intrinsics.Object[symbolForHarden] = tamedHarden;

  const hostIntrinsics = { __proto__: null };

  // The Node.js Buffer is a derived class of Uint8Array, and as such is often
  // passed around where a Uint8Array is expected.
  if (typeof globalThis.Buffer === 'function') {
    hostIntrinsics.Buffer = globalThis.Buffer;
  }

  /**
   * Wrap console unless suppressed.
   * At the moment, the console is considered a host power in the start
   * compartment, and not a primordial. Hence it is absent from the whilelist
   * and bypasses the intrinsicsCollector.
   *
   * @type {((error: any) => string | undefined) | undefined}
   */
  let optGetStackString;
  if (errorTaming === 'safe') {
    optGetStackString = intrinsics['%InitialGetStackString%'];
  }
  const consoleRecord = tameConsole(
    consoleTaming,
    errorTrapping,
    unhandledRejectionTrapping,
    optGetStackString,
  );
  globalThis.console = /** @type {Console} */ (consoleRecord.console);

  // The untamed Node.js console cannot itself be hardened as it has mutable
  // internal properties, but some of these properties expose internal versions
  // of classes from node's "primordials" concept.
  // eslint-disable-next-line no-underscore-dangle
  if (typeof (/** @type {any} */ (consoleRecord.console)._times) === 'object') {
    // SafeMap is a derived Map class used internally by Node
    // There doesn't seem to be a cleaner way to reach it.
    hostIntrinsics.SafeMap = getPrototypeOf(
      // eslint-disable-next-line no-underscore-dangle
      /** @type {any} */ (consoleRecord.console)._times,
    );
  }

  // The default `assert` installed by `assert-shim.js` does not redact errors,
  // leaving `lockdown` or `repairIntrinsics` with the obligation to replace it
  // with a redacting version, unless the caller opts-out with errorTaming set
  // to `unsafe` or `unsafe-debug`.
  // The inverse was true through version 1.13.0, except the configuration
  // was disregarded and the redacting `assert` left in place if lexical
  // `assert` differed from `globalThis.assert`.
  // @ts-ignore assert is absent on globalThis type def.
  if (errorTaming !== 'unsafe' && errorTaming !== 'unsafe-debug') {
    globalThis.assert = makeAssert();
  }

  // Replace *Locale* methods with their non-locale equivalents
  tameLocaleMethods(intrinsics, localeTaming);

  tameFauxDataProperties(intrinsics);

  /**
   * 2. Enforce PERMITS on shared intrinsics
   */

  // Remove non-standard properties.
  // All remaining functions encountered during whitelisting are
  // branded as honorary native functions.
  reportInGroup(
    'SES Removing unpermitted intrinsics',
    reporter,
    groupReporter =>
      removeUnpermittedIntrinsics(
        intrinsics,
        markVirtualizedNativeFunction,
        groupReporter,
      ),
  );

  // Initialize the powerful initial global, i.e., the global of the
  // start compartment, from the intrinsics.

  setGlobalObjectConstantProperties(globalThis);

  setGlobalObjectMutableProperties(globalThis, {
    intrinsics,
    newGlobalPropertyNames: initialGlobalPropertyNames,
    makeCompartmentConstructor,
    markVirtualizedNativeFunction,
  });

  if (
    evalTaming === 'no-eval' ||
    // deprecated
    evalTaming === 'noEval'
  ) {
    setGlobalObjectEvaluators(
      globalThis,
      noEvalEvaluate,
      markVirtualizedNativeFunction,
    );
  } else if (
    evalTaming === 'safe-eval' ||
    // deprecated
    evalTaming === 'safeEval'
  ) {
    const { safeEvaluate } = makeSafeEvaluator({ globalObject: globalThis });
    setGlobalObjectEvaluators(
      globalThis,
      safeEvaluate,
      markVirtualizedNativeFunction,
    );
  } else if (
    evalTaming === 'unsafe-eval' ||
    // deprecated
    evalTaming === 'unsafeEval'
  ) {
    // Leave eval function and Function constructor of the initial
    // compartment intact.
    // Other compartments will not have access to these evaluators unless a
    // guest program escapes containment.
  }

  /**
   * 3. HARDEN to share the intrinsics.
   *
   * We define hardenIntrinsics here so that options are in scope, but return
   * it to the caller because we intend to eventually allow vetted shims to run
   * between repairs and the hardening of intrinsics and so we can benchmark
   * repair separately from hardening.
   */

  const hardenIntrinsics = () => {
    priorHardenIntrinsics === undefined ||
      // eslint-disable-next-line @endo/no-polymorphic-call
      assert.fail(
        X`Already locked down at ${priorHardenIntrinsics} (SES_ALREADY_LOCKED_DOWN)`,
        TypeError,
      );
    // See https://github.com/endojs/endo/blob/master/packages/ses/error-codes/SES_ALREADY_LOCKED_DOWN.md
    priorHardenIntrinsics = TypeError(
      'Prior lockdown (SES_ALREADY_LOCKED_DOWN)',
    );
    // Tease V8 to generate the stack string and release the closures the stack
    // trace retained:
    priorHardenIntrinsics.stack;

    // Circumvent the override mistake.
    // TODO consider moving this to the end of the repair phase, and
    // therefore before vetted shims rather than afterwards. It is not
    // clear yet which is better.
    // @ts-ignore enablePropertyOverrides does its own input validation
    reportInGroup('SES Enabling property overrides', reporter, groupReporter =>
      enablePropertyOverrides(
        intrinsics,
        overrideTaming,
        groupReporter,
        overrideDebug,
      ),
    );
    if (legacyRegeneratorRuntimeTaming === 'unsafe-ignore') {
      tameRegeneratorRuntime();
    }

    // Finally register and optionally freeze all the intrinsics. This
    // must be the operation that modifies the intrinsics.
    const toHarden = {
      intrinsics,
      hostIntrinsics,
      globals: {
        // Harden evaluators
        Function: globalThis.Function,
        eval: globalThis.eval,
        // @ts-ignore Compartment does exist on globalThis
        Compartment: globalThis.Compartment,

        // Harden Symbol
        Symbol: globalThis.Symbol,
      },
    };

    // Harden Symbol and properties for initialGlobalPropertyNames in the host realm
    for (const prop of getOwnPropertyNames(initialGlobalPropertyNames)) {
      toHarden.globals[prop] = globalThis[prop];
    }

    tamedHarden(toHarden);

    return tamedHarden;
  };

  return hardenIntrinsics;
};$h͏_once.repairIntrinsics(repairIntrinsics);
})()
,
// === 59. ses ./src/lockdown-shim.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let globalThis,repairIntrinsics;$h͏_imports([["./assert-sloppy-mode.js", []],["./commons.js", [["globalThis",[$h͏_a => (globalThis = $h͏_a)]]]],["./lockdown.js", [["repairIntrinsics",[$h͏_a => (repairIntrinsics = $h͏_a)]]]]]);








/** @import {LockdownOptions} from '../types.js' */

/**
 * @param {LockdownOptions} [options]
 */
globalThis.lockdown = options => {
  const hardenIntrinsics = repairIntrinsics(options);
  globalThis.harden = hardenIntrinsics();
};

/**
 * @param {LockdownOptions} [options]
 */
globalThis.repairIntrinsics = options => {
  const hardenIntrinsics = repairIntrinsics(options);
  // Reveal hardenIntrinsics after repairs.
  globalThis.hardenIntrinsics = () => {
    // Reveal harden after hardenIntrinsics.
    // Harden is dangerous before hardenIntrinsics because hardening just
    // about anything will inadvertently render intrinsics irreparable.
    // Also, for modules that must work both before or after lockdown (code
    // that is portable between JS and SES), the existence of harden in global
    // scope signals whether such code should attempt to use harden in the
    // defense of its own API.
    // @ts-ignore harden not yet recognized on globalThis.
    globalThis.harden = hardenIntrinsics();
  };
};
})()
,
// === 60. ses ./src/compartment-shim.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let globalThis,makeCompartmentConstructor,tameFunctionToString,getGlobalIntrinsics,chooseReporter;$h͏_imports([["./commons.js", [["globalThis",[$h͏_a => (globalThis = $h͏_a)]]]],["./compartment.js", [["makeCompartmentConstructor",[$h͏_a => (makeCompartmentConstructor = $h͏_a)]]]],["./tame-function-tostring.js", [["tameFunctionToString",[$h͏_a => (tameFunctionToString = $h͏_a)]]]],["./intrinsics.js", [["getGlobalIntrinsics",[$h͏_a => (getGlobalIntrinsics = $h͏_a)]]]],["./reporting.js", [["chooseReporter",[$h͏_a => (chooseReporter = $h͏_a)]]]]]);





const markVirtualizedNativeFunction = tameFunctionToString();

const muteReporter = chooseReporter('none');

// @ts-ignore Compartment is definitely on globalThis.
globalThis.Compartment = makeCompartmentConstructor(
  makeCompartmentConstructor,
  // Any reporting that would need to be done should have already been done
  // during `lockdown()`.
  // See https://github.com/endojs/endo/pull/2624#discussion_r1840979770
  getGlobalIntrinsics(globalThis, muteReporter),
  markVirtualizedNativeFunction,
  {
    enforceNew: true,
  },
);
})()
,
// === 61. ses ./src/assert-shim.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let globalThis,makeAssert;$h͏_imports([["./commons.js", [["globalThis",[$h͏_a => (globalThis = $h͏_a)]]]],["./error/assert.js", [["makeAssert",[$h͏_a => (makeAssert = $h͏_a)]]]]]);


globalThis.assert = makeAssert(undefined, true);
})()
,
// === 62. ses ./src/console-shim.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';let symbolFor,globalThis,defineCausalConsoleFromLogger,loggedErrorHandler;$h͏_imports([["./commons.js", [["symbolFor",[$h͏_a => (symbolFor = $h͏_a)]],["globalThis",[$h͏_a => (globalThis = $h͏_a)]]]],["./error/console.js", [["defineCausalConsoleFromLogger",[$h͏_a => (defineCausalConsoleFromLogger = $h͏_a)]]]],["./error/assert.js", [["loggedErrorHandler",[$h͏_a => (loggedErrorHandler = $h͏_a)]]]]]);



// TODO possible additional exports. Some are privileged.
// export { loggedErrorHandler };
// export {
//   makeCausalConsole,
//   consoleLevelMethods,
//   consoleOtherMethods,
//   makeLoggingConsoleKit,
//   filterConsole,
//   pumpLogToConsole,
// } from './src/error/console.js';
// export { assertLogs, throwsAndLogs } from './src/error/throws-and-logs.js';

/**
 * Makes a Console like the
 * [SES causal `console`](https://github.com/endojs/endo/blob/master/packages/ses/src/error/README.md)
 * but whose output is redirected to the supplied `logger` function.
 */
const makeCausalConsoleFromLoggerForSesAva =
  defineCausalConsoleFromLogger(loggedErrorHandler);

/**
 *`makeCausalConsoleFromLoggerForSesAva` is privileged because it exposes
 * unredacted error info onto the `Logger` provided by the caller. It
 * should not be made available to non-privileged code.
 *
 * Further, we consider this particular API choice to be experimental
 * and may change in the future. It is currently only intended for use by
 * `@endo/ses-ava`, with which it will be co-maintained.
 *
 * Thus, this `console-shim.js` makes `makeCausalConsoleFromLoggerForSesAva`
 * available on `globalThis` which it *assumes* is the global of the start
 * compartment and is therefore allowed to hold powers that should not be
 * available in constructed compartments. It makes it available as the value of
 * a global property named by a registered symbol named
 * `MAKE_CAUSAL_CONSOLE_FROM_LOGGER_KEY_FOR_SES_AVA`.
 *
 * Anyone accessing this, including `@endo/ses-ava`, should feature test for
 * this and be tolerant of its absence. It may indeed disappear from later
 * versions of the ses-shim.
 */
const MAKE_CAUSAL_CONSOLE_FROM_LOGGER_KEY_FOR_SES_AVA = symbolFor(
  'MAKE_CAUSAL_CONSOLE_FROM_LOGGER_KEY_FOR_SES_AVA',
);

globalThis[MAKE_CAUSAL_CONSOLE_FROM_LOGGER_KEY_FOR_SES_AVA] =
  makeCausalConsoleFromLoggerForSesAva;
})()
,
// === 63. ses ./index.js ===
({imports:$h͏_imports,liveVar:$h͏_live,onceVar:$h͏_once,import:$h͏_import,importMeta:$h͏____meta})=>(function(){'use strict';$h͏_imports([["./src/lockdown-shim.js", []],["./src/compartment-shim.js", []],["./src/assert-shim.js", []],["./src/console-shim.js", []]]);
})()
,
])()
;/*! end SES */
(()=>{"use strict";var e={},t={};function r(a){var s=t[a];if(void 0!==s)return s.exports;var o=t[a]={id:a,loaded:!1,exports:{}};return e[a].call(o.exports,o,o.exports,r),o.loaded=!0,o.exports}r.m=e,globalThis.location;var a=globalThis.setTimeout,s=globalThis.clearTimeout,o=globalThis.document,n=(globalThis.trustedTypes,globalThis.self);let c=[];r.amdO={},(()=>{var e=[];r.O=(t,a,s,o)=>{if(a){o=o||0;for(var n=e.length;n>0&&e[n-1][2]>o;n--)e[n]=e[n-1];e[n]=[a,s,o];return}for(var c=1/0,n=0;n<e.length;n++){for(var[a,s,o]=e[n],l=!0,i=0;i<a.length;i++)(!1&o||c>=o)&&Object.keys(r.O).every(e=>r.O[e](a[i]))?a.splice(i--,1):(l=!1,o<c&&(c=o));if(l){e.splice(n--,1);var m=s();void 0!==m&&(t=m)}}return t}})(),r.n=e=>{var t=e&&e.__esModule?()=>e.default:()=>e;return r.d(t,{a:t}),t},(()=>{var e,t=Object.getPrototypeOf?e=>Object.getPrototypeOf(e):e=>e.__proto__;r.t=function(a,s){if(1&s&&(a=this(a)),8&s||"object"==typeof a&&a&&(4&s&&a.__esModule||16&s&&"function"==typeof a.then))return a;var o=Object.create(null);r.r(o);var n={};e=e||[null,t({}),t([]),t(t)];for(var c=2&s&&a;("object"==typeof c||"function"==typeof c)&&!~e.indexOf(c);c=t(c))Object.getOwnPropertyNames(c).forEach(e=>n[e]=()=>a[e]);return n.default=()=>a,r.d(o,n),o}})(),r.d=(e,t)=>{for(var a in t)r.o(t,a)&&!r.o(e,a)&&Object.defineProperty(e,a,{enumerable:!0,get:t[a]})},r.f={},r.e=e=>Promise.all(Object.keys(r.f).reduce((t,a)=>(r.f[a](e,t),t),[])),r.u=e=>""+e+"."+({46:"8e08e6e02ee5b410f4b7",78:"3f5c2f0623cbb89fed65",110:"15b564d74f154f026d49",133:"e874c02a755027a6acbb",185:"82c355699929122eb5fc",229:"c5106ca0dd2506d21430",339:"6f31b5fbfe9c136caad1",343:"9f04d5cced645d830c68",407:"2d06e22522d5a272e731",418:"7ec182b82d5aa45511ab",425:"7e8d99dee1bfff509ad2",427:"20efcf4d55bc96c8b85a",461:"0f15c40804e2d4b953d5",463:"f2a863f6dd0d5c51d1ab",483:"459fd9dc91733f590cfd",634:"a374cf2e9daec1d343d3",659:"c6f98b51274fcf8eda7b",670:"879743495fa598281d1e",836:"114c3ee7c0b1da55b62a",891:"9e09a7234c12e8d26a70",904:"dae7eed8602d5c28f69f",1105:"31eb31e7c0fad0886b7d",1122:"47780f917620d99b7a9e",1290:"cdc4348726f321e83845",1309:"3a22869c4c7111b984ff",1331:"2718d851431bd325ee49",1391:"68c35be81337a1b93973",1507:"adddc3828ec94e3a13ba",1523:"65307d5de81b1d7128a5",1598:"32687abcd971ba8d5b38",1728:"00fffe6def3ea228dfea",1768:"5941a27263127f095ba3",1791:"291ddec70a44c104ef56",1826:"cceb751f62d12b18d570",1863:"a63f88b858a95a81daaf",1864:"5f74bcb29072bcc6a9f3",1887:"ecefc9b5527cb031d4c9",2160:"912cb345b22bcb92a417",2186:"a3b8ac4ce309b0f4a23b",2189:"9162e9470bffba239236",2203:"a90c2c39ff8615ffbbab",2213:"2629447fe946aa3f4ba0",2430:"5ebb63d79e623c8426bd",2445:"3a26db97c7a448bed2e4",2449:"2549480c338a20e0aea1",2514:"09d453af9b7c1435c97e",2584:"8d8902f5e06f7a9c04e5",2638:"d4f25964e2e27c38b95c",2664:"07817a8de0f4cf5c5aa0",2710:"e336c9b8a77c4c33d66d",2721:"4f985d6675abb40b5666",2747:"6f9392f3d6b120376c2c",2962:"318baf55dde61f8d294c",3139:"3fd38a4cb408b5971eda",3186:"1e00a2217e7a4e2013f1",3375:"4580f65109599f1e14d4",3400:"5651533cd374ae2d553c",3404:"2de8716c62b315613d78",3740:"33faa4f34059e80ff3ac",3785:"3f2245cf7b407147d214",3809:"9a24840f4d9f99ea267e",3881:"f61c7ce97557a4c4598a",3885:"9b859b8d609945c9e261",3931:"6461e4a66b61d4d826bd",3956:"ea718711635609d76ccd",4052:"3912f755a691b9da6395",4073:"0748015796f8b5b2b6b4",4113:"ce87e499c347a28e2bcb",4243:"14e87449205780863b52",4274:"a081aef0859fb221e22f",4323:"c20809934d487acf60ab",4480:"192300234b6c37d293d2",4520:"db449bf83fc2b95f3b88",4579:"26ef71b35e42413a402e",4593:"541404a6849b7fb544af",4753:"d020d84ac012a85e4351",4781:"21462be34f8be1385025",4859:"897c95113f6dfd9695c6",5087:"eea522347b9e2da7c252",5098:"92400c4cc1add5a17276",5151:"856ee585d6c214f91e9c",5175:"8ec5cf80476a849de1b8",5297:"3eaea93cfd9c9afd46cc",5458:"fa168e7ff63713997bbd",5609:"a8471b7b5652123328d7",5616:"9f123d3f3d255f06fce8",5657:"d1ac9e7d6e7e04609ab1",5671:"61b55874fdadaf5da1fe",6053:"45520ad50c2c7927bcdd",6141:"a1dc8853d541af541843",6336:"7f3f069e04cf6c251d88",6358:"f240e0b18d7f9bcc29d8",6401:"fd0961664f365a281da4",6622:"3cd7b616ce7880d82728",6649:"dca338e09ee54d7ddcad",6802:"a173920b782dcbc96cef",6828:"969a9e214950a943227a",6906:"bb62a58620bc154d2e1c",7064:"03fc7cbaff511d264c3f",7160:"83bdfc98398e213e096d",7219:"99092a42b8b540bae36d",7449:"dcf0758e4e99885f4da3",7622:"6f40576ad965ce2f4864",7651:"2605229727a87732bb99",7755:"3e5739adf757a5b3dd9b",7899:"d3d5afbf0f8abab37f8b",7980:"c105b675d1e2568f8ed9",7998:"35a011201f37b242fc1e",8015:"2f0bccbb3ad01620760a",8063:"d4d4568e1c7562cfcac2",8093:"d296fc77343c776d3b80",8102:"671a4bd7c61f3d83d370",8264:"04591084648a1796d9ef",8364:"39850e7b7e04648c440a",8528:"07914587e8c494219bb4",8650:"cc59f1089380147e5865",8734:"ed40444632ebff40ed0c",8792:"aa2f609cbd5bd75a63ea",8811:"22b6bdfad91f2de8053f",8927:"cd844724d340b21afc40",8935:"0c851c93c46644cb3227",8994:"d75f0420c8aac1e8f355",9038:"3db49b6563f2bb2eec14",9060:"4af39d0c4a0ec794cb64",9165:"43fb707d270a60163860",9232:"abd09840df18f90fe1ed",9277:"e44ea4e370c2c458a909",9281:"653d0784c67c29988968",9354:"81bf99c8dd139051029a",9600:"5880cb093fb6f76e674b",9674:"562a7b01c906b3c0f7c8",9689:"50b9619a068e9234be3b",9737:"d27a7bc6726e603b0d21",9807:"71118922e585841f2be8",9861:"14d1bc2c2babddf5f450",9949:"ef120a55c9f26731aeb9",9957:"6095ed1d273fb9705835"})[e]+".js",r.hmd=e=>((e=Object.create(e)).children||(e.children=[]),Object.defineProperty(e,"exports",{enumerable:!0,set:()=>{throw Error("ES Modules may not assign module.exports or exports.*, Use ESM export syntax, instead: "+e.id)}}),e),r.o=(e,t)=>Object.prototype.hasOwnProperty.call(e,t),(()=>{var e={};r.l=(t,n,c,l)=>{if(e[t])return void e[t].push(n);if(void 0!==c)for(var i,m,p=o.getElementsByTagName("script"),u=0;u<p.length;u++){var h=p[u];if(h.getAttribute("src")==t){i=h;break}}i||(m=!0,(i=o.createElement("script")).charset="utf-8",r.nc&&i.setAttribute("nonce",r.nc),i.src=t),e[t]=[n];var g=(r,a)=>{i.onerror=i.onload=null,s(d);var o=e[t];if(delete e[t],i.parentNode&&i.parentNode.removeChild(i),o&&o.forEach(e=>e(a)),r)return r(a)},d=a(g.bind(null,void 0,{type:"timeout",target:i}),12e4);i.onerror=g.bind(null,i.onerror),i.onload=g.bind(null,i.onload),m&&o.head.appendChild(i)}})(),r.r=e=>{"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},r.nmd=e=>(e.paths=[],e.children||(e.children=[]),e),c.push(e=>{"function"!=typeof SNOW&&(()=>{let e;var t,r,a,s={586:(e,t,r)=>{let a=r(228),{getFramesArray:s,getFrameTag:o}=r(648),{getOnload:n,setOnload:c,removeAttribute:l,addEventListener:i}=r(14);e.exports=function(e){for(let t=0;t<e.length;t++){let r=s(e[t],!0);for(let e=0;e<r.length;e++)!function(e){if(!o(e))return;i(e,"load",function(){a(e)});let t=n(e);t&&(c(e,null),l(e,"onload"),c(e,t))}(r[e])}}},750:(e,t,r)=>{let{Object:a}=r(14);e.exports=function(e){e&&a.getOwnPropertyDescriptor(e,"")}},407:e=>{let t=Object.getOwnPropertyDescriptor(window,"length").get,r=t.bind(window),a=Object.getOwnPropertyDescriptor(Document.prototype,"createElement").value.bind(o),s=Object.getOwnPropertyDescriptor(Node.prototype,"appendChild").value.bind(o.documentElement),n=Object.getOwnPropertyDescriptor(Node.prototype,"removeChild").value.bind(o.documentElement);e.exports={getLength:t,runInNewRealm:function(e){let t=r(),o=a("IFRAME");s(o);let c=e(window[t]);return n(o),c}}},832:(e,t,r)=>{let{Object:a,Function:s}=r(14),{isTagFramable:o}=r(648),{error:n,ERR_EXTENDING_FRAMABLES_BLOCKED:c}=r(312);e.exports=function(e){let t=a.getOwnPropertyDescriptor(e.CustomElementRegistry.prototype,"define");t.configurable=t.writable=!0;let r=t.value;t.value=function(e,t,a){if(a&&o(a.extends+""))throw n(c,e,a);return s.prototype.call.call(r,this,e,t,a)},a.defineProperty(e.CustomElementRegistry.prototype,"define",t)}},228:(e,t,r)=>{let a=r(750),{getLength:s}=r(407),{shadows:o,toArray:n,getFramesArray:c,getContentWindowOfFrame:l,getOwnerWindowOfNode:i}=r(648),{Object:m,getFrameElement:p,Function:u,isConnected:h}=r(14),{forEachOpened:g}=r(134);function d(e,t){let r=function e(t,r){var a;let n=u.prototype.call.call(s,t);for(let s=0;s<n;s++){if(a=t[s],null===m.getPrototypeOf.call(t,a))continue;if(p(t[s])===r)return t[s];let o=e(t[s],r);if(o)return o}for(let a=0;a<o.length;a++){let s=o[a];if(!h(s)||i(s)!==t)continue;let n=c(s,!1);for(let t=0;t<n.length;t++){let a=n[t],s=l(a);if(a===r)return s;let o=e(s,r);if(o)return o}}return null}(e,t);return r&&top.SNOW_WINDOW(r),!!r}e.exports=function(e){e=n(e);for(let t=0;t<e.length;t++){let r=e[t];"object"==typeof r&&null!==r&&(a(r),d(top,r)||g(d,r))}}},328:(e,t,r)=>{let{getFramesArray:a,getDeclarativeShadows:s}=r(648),{document:o,getChildElementCount:n,setInnerHTML:c}=r(14),{error:l,ERR_DECLARATIVE_SHADOWS_BLOCKED:i,ERR_HTML_FRAMES_SRCDOC_BLOCKED:m}=r(312);e.exports={assertHTML:function(e){for(let t=0;t<e.length;t++){let r=o.createElement("html");if(c(r,e[t]),n(r)){if(s(r).length>0)throw l(i,e[t]);let o=a(r,!1);for(let a=0;a<o.length;a++){let s=o[a];if(r.getAttribute.call(s,"srcdoc"))throw l(m,e[t])}}}}}},352:(e,t,r)=>{let a=r(228),s=r(716),o=r(832),n=r(583),c=r(278),l=r(459),i=r(58),m=r(744),p=r(294),{hookShadowDOM:u}=r(373),{Array:h,push:g,addEventListener:d,getFrameElement:b}=r(14),{makeDescriptorSetter:k}=r(648),{isMarked:y,mark:f}=r(111),{error:j,ERR_CB_MUST_BE_FUNCTION:w,ERR_MARK_NEW_WINDOW_FAILED:v}=r(312),x=k("SNOW_WINDOW",function(e){O(e)}),E=k("SNOW_FRAME",function(e){a(e)}),T=k("SNOW",q);function O(e,t,r){if(!r&&function e(t){try{let e=!y(t);return e&&f(t),e}catch(e){j(v,t,e)}return e(t)}(e)){T(e),function(e){let t=b(e);d(t,"load",function(){a(t)})}(e),s(e),o(e),n(e),c(e),l(e,"load"),i(e),u(e),p(e),m(e);for(let t=0;t<_.length;t++)if(_[t](e))return}t&&t(e)}let _=new h;function q(e,t){if("function"!=typeof e&&j(w,e))return;x(top),E(top);let r=1===g(_,e),a=t||window;O(a,e,!r&&a===top)}e.exports=q},58:(e,t,r)=>{let{error:a,ERR_NON_TOP_DOCUMENT_WRITE_BLOCKED:s}=r(312),{protectShadows:o}=r(373),n=r(586),{getFramesArray:c,shadows:l}=r(648),{getParentElement:i,getCommonAncestorContainer:m,slice:p,Object:u,Function:h}=r(14),{assertHTML:g}=r(328),d=r(228),b={Range:["insertNode"],DocumentFragment:["replaceChildren","append","prepend"],Document:["replaceChildren","append","prepend","write","writeln","execCommand"],Node:["appendChild","insertBefore","replaceChild"],Element:["innerHTML","outerHTML","insertAdjacentHTML","replaceWith","insertAdjacentElement","append","before","prepend","after","replaceChildren"],ShadowRoot:["innerHTML"],HTMLIFrameElement:["srcdoc"]},k=u.getOwnPropertyNames(b);e.exports=function(e){for(let t=0;t<k.length;t++){let r=k[t],y=b[r];for(let t=0;t<y.length;t++){let b=y[t],k=u.getOwnPropertyDescriptor(e[r].prototype,b);if(!k)continue;let f=k.set?"set":"value",j="Range"===r,w="write"===b||"writeln"===b;k[f]=function(e,t,r){return function(){if(r&&this!==top.document)throw a(s,this);let u=p(arguments),b=t?m(this):i(this)||this;n(u),n(l),g(u);let k=h.prototype.apply.call(e,this,u);return d(c(b,!1)),d(u),o(!0),k}}(k[f],j,w),k.configurable=!0,"value"===f&&(k.writable=!0),u.defineProperty(e[r].prototype,b,k)}}}},459:(e,t,r)=>{let a=r(228),{removeEventListener:s,addEventListener:o,slice:n,Map:c,Object:l}=r(14),i=new c;e.exports=function(e,t){l.defineProperty(e.EventTarget.prototype,"addEventListener",{configurable:!0,writable:!0,value:function(r,s,c){let l=s;return r===t&&(i.has(s)||i.set(s,function(){a(this);let e=n(arguments);s&&(s.handleEvent?s.handleEvent.apply(s,e):s.apply(this,e))}),l=i.get(s)),o(this||e,r,l,c)}}),l.defineProperty(e.EventTarget.prototype,"removeEventListener",{configurable:!0,writable:!0,value:function(r,a,o){let n=a;return r===t&&(n=i.get(a),i.delete(a)),s(this||e,r,n,o)}})}},312:e=>{let{Error:t}=globalThis,{from:r}=Array,a=Function.prototype.apply.bind(console.error,console);function s(e){let s=r(arguments);return a(s),new t(e)}function o(e){return`SNOW ERROR (CODE:${e}):`}e.exports={error:function(e,t,r,a){switch(e){case 7:return s(o(7),`blocking ${r} object:`,t,`of type "${a}" (not in allow list)`,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/87#issuecomment-1586868353",".");case 6:return s(o(6),`blocking extension attempt ("${t}") of framable elements such as provided`,r,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/56#issuecomment-1374899809",".");case 1:return s(o(1),"failed to mark new window:",t,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/33#issuecomment-1239280063",".","in order to maintain a bulletproof defense mechanism, failing to mark a new window typically causes an infinite loop",".","error caught:",r);case 2:return s(o(2),'first argument must be of type "function", instead got:',t,".","therefore, snow bailed and is not applied to the page until this is fixed.");case 3:return s(o(3),'blocking open attempt to "javascript:" url:',t,"by window: ",r,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/44#issuecomment-1369687802",".");case 4:return s(o(4),"blocking access to property:",`"${t}"`,"of opened window: ",r,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/2#issuecomment-1239264255",".");case 5:return s(o(5),"blocking html string that includes a representation of a declarative shadow:",`"${t}"`,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/32#issuecomment-1239273328",".");case 8:return s(o(8),'blocking html string that includes a representation of a framable element with the "srcdoc" attribute:',`"${t}"`,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/???",".");case 9:return s(o(9),"blocking document.write\\ln action on a document that is not the top most document:",t,".","if this prevents your application from running correctly, please visit/report at","https://github.com/LavaMoat/snow/issues/???",".")}},generateErrorMessage:o,ERR_MARK_NEW_WINDOW_FAILED:1,ERR_OPENED_PROP_ACCESS_BLOCKED:4,ERR_OPEN_JS_SCHEME_BLOCKED:3,ERR_CB_MUST_BE_FUNCTION:2,ERR_DECLARATIVE_SHADOWS_BLOCKED:5,ERR_EXTENDING_FRAMABLES_BLOCKED:6,ERR_BLOB_TYPE_BLOCKED:7,ERR_HTML_FRAMES_SRCDOC_BLOCKED:8,ERR_NON_TOP_DOCUMENT_WRITE_BLOCKED:9}},111:(e,t,r)=>{let{Map:a,Object:s,Array:o}=r(14),n=new o,c=new a;e.exports={isMarked:function(e){if(!c.has(e))return!1;let t=s.getOwnPropertyDescriptor(e,"SNOW_ID");if(!t||!s.hasOwnProperty.call(t,"value")||"function"!=typeof t.value)return!1;let r=c.get(e);return t.value(n)===r},mark:function(e){let t=new o,r=s.create(null);r.value=e=>e===n&&t,s.defineProperty(e,"SNOW_ID",r),c.set(e,t)}}},14:(e,t,r)=>{let{runInNewRealm:a}=r(407);e.exports=function(e){let t=function(e){let{EventTarget:t}=e;return a(function(e){let{URL:r,Proxy:a,JSON:s,Attr:o,String:n,Function:c,Map:l,Node:i,Document:m,DocumentFragment:p,Blob:u,ShadowRoot:h,Object:g,Reflect:d,Array:b,Element:k,HTMLElement:y,Range:f,HTMLIFrameElement:j,HTMLFrameElement:w,HTMLObjectElement:v}=e,x={URL:r,Proxy:a,JSON:s,Attr:o,String:n,Function:c,Map:l,Node:i,Document:m,DocumentFragment:p,Blob:u,ShadowRoot:h,Object:g,Reflect:d,Array:b,Element:k,HTMLElement:y,Range:f,EventTarget:t,HTMLIFrameElement:j,HTMLFrameElement:w,HTMLObjectElement:v};return x.document={createElement:e.document.createElement.bind(e.document)},x})}(e),{document:r,Proxy:s,Function:o,String:n,Map:c,Node:l,Document:i,DocumentFragment:m,Blob:p,ShadowRoot:u,Object:h,Reflect:g,Array:d,Element:b,HTMLElement:k,Range:y,EventTarget:f,HTMLIFrameElement:j,HTMLFrameElement:w,HTMLObjectElement:v}=t;return h.assign(t,{iframeContentWindow:h.getOwnPropertyDescriptor(j.prototype,"contentWindow").get,frameContentWindow:h.getOwnPropertyDescriptor(w.prototype,"contentWindow").get,objectContentWindow:h.getOwnPropertyDescriptor(v.prototype,"contentWindow").get,createElement:h.getOwnPropertyDescriptor(i.prototype,"createElement").value,slice:h.getOwnPropertyDescriptor(d.prototype,"slice").value,push:h.getOwnPropertyDescriptor(d.prototype,"push").value,split:h.getOwnPropertyDescriptor(n.prototype,"split").value,nodeType:h.getOwnPropertyDescriptor(l.prototype,"nodeType").get,isConnected:h.getOwnPropertyDescriptor(l.prototype,"isConnected").get,tagName:h.getOwnPropertyDescriptor(b.prototype,"tagName").get,getInnerHTML:h.getOwnPropertyDescriptor(b.prototype,"innerHTML").get,setInnerHTML:h.getOwnPropertyDescriptor(b.prototype,"innerHTML").set,toString:h.getOwnPropertyDescriptor(h.prototype,"toString").value,getOnload:h.getOwnPropertyDescriptor(k.prototype,"onload").get,setOnload:h.getOwnPropertyDescriptor(k.prototype,"onload").set,getAttribute:h.getOwnPropertyDescriptor(b.prototype,"getAttribute").value,setAttribute:h.getOwnPropertyDescriptor(b.prototype,"setAttribute").value,removeAttribute:h.getOwnPropertyDescriptor(b.prototype,"removeAttribute").value,remove:h.getOwnPropertyDescriptor(b.prototype,"remove").value,addEventListener:h.getOwnPropertyDescriptor(f.prototype,"addEventListener").value,removeEventListener:h.getOwnPropertyDescriptor(f.prototype,"removeEventListener").value,getChildElementCount:h.getOwnPropertyDescriptor(b.prototype,"childElementCount").get,getFrameElement:h.getOwnPropertyDescriptor(e,"frameElement").get,getParentElement:h.getOwnPropertyDescriptor(l.prototype,"parentElement").get,getOwnerDocument:h.getOwnPropertyDescriptor(l.prototype,"ownerDocument").get,getDefaultView:h.getOwnPropertyDescriptor(i.prototype,"defaultView").get,getBlobFileType:h.getOwnPropertyDescriptor(p.prototype,"type").get,getPreviousElementSibling:h.getOwnPropertyDescriptor(b.prototype,"previousElementSibling").get,getCommonAncestorContainer:h.getOwnPropertyDescriptor(y.prototype,"commonAncestorContainer").get}),{document:r,Proxy:s,Object:h,Reflect:g,Function:o,Node:l,Element:b,Document:i,DocumentFragment:m,Blob:p,ShadowRoot:u,Array:d,Map:c,getContentWindow:function(e,r){switch(r){case"IFRAME":return t.iframeContentWindow.call(e);case"FRAME":return t.frameContentWindow.call(e);case"OBJECT":return t.objectContentWindow.call(e);default:return null}},stringToLowerCase:function(e){return t.String.prototype.toLowerCase.call(e)},stringStartsWith:function(e,r){return t.String.prototype.startsWith.call(e,r)},parse:function(e,r){return t.JSON.parse(e,r)},stringify:function(e,r,a){return t.JSON.stringify(e,r,a)},slice:function(e,r,a){return t.slice.call(e,r,a)},push:function(e,r){return t.push.call(e,r)},split:function(e,r){return t.split.call(e,r)},nodeType:function(e){return t.nodeType.call(e)},isConnected:function(e){return t.isConnected.call(e)},tagName:function(e){return t.tagName.call(e)},toString:function(e){return t.toString.call(e)},getOnload:function(e){return t.getOnload.call(e)},setOnload:function(e,r){return t.setOnload.call(e,r)},remove:function(e){return t.remove.call(e)},removeAttribute:function(e,r){return t.removeAttribute.call(e,r)},getAttribute:function(e,r){return t.getAttribute.call(e,r)},setAttribute:function(e,r,a){return t.setAttribute.call(e,r,a)},addEventListener:function(e,r,a,s){return t.Function.prototype.call.call(t.addEventListener,e,r,a,s)},removeEventListener:function(e,r,a,s){return t.Function.prototype.call.call(t.removeEventListener,e,r,a,s)},createElement:function(e,r,a){return t.createElement.call(e,r,a)},getInnerHTML:function(e){return t.getInnerHTML.call(e)},setInnerHTML:function(e,r){return t.setInnerHTML.call(e,r)},getChildElementCount:function(e){return t.getChildElementCount.call(e)},getFrameElement:function(e){return t.Function.prototype.call.call(t.getFrameElement,e)},getParentElement:function(e){return t.getParentElement.call(e)},getOwnerDocument:function(e){return t.getOwnerDocument.call(e)},getDefaultView:function(e){return t.getDefaultView.call(e)},getBlobFileType:function(e){return t.getBlobFileType.call(e)},getPreviousElementSibling:function(e){return t.getPreviousElementSibling.call(e)},getCommonAncestorContainer:function(e){return t.getCommonAncestorContainer.call(e)}}}(top)},583:(e,t,r)=>{let{stringToLowerCase:a,stringStartsWith:s,slice:o,Function:n,Object:c}=r(14),{error:l,ERR_OPEN_JS_SCHEME_BLOCKED:i}=r(312),{proxy:m,getProxyByOpened:p}=r(134);function u(e){let t=c.getOwnPropertyDescriptor(e.MessageEvent.prototype,"source"),r=t.get;t.get=function(){let e=r.call(this);return p(e)||e},c.defineProperty(e.MessageEvent.prototype,"source",t)}function h(e,t,r,c){return r(e),function(){let r=o(arguments),p=r[0];if(s(a(p+""),"javascript"))throw l(i,p+"",e);let u=n.prototype.apply.call(t,this,r);return u?!c&&r.length<3?u:m(u):null}}e.exports=function(e){c.defineProperty(e,"open",{value:h(e,e.open,u,!0)}),c.defineProperty(e.Document.prototype,"open",{value:h(e,e.document.open,u,!1)})}},134:(e,t,r)=>{let{Object:a,Proxy:s,Reflect:o,Map:n}=r(14),{error:c,ERR_OPENED_PROP_ACCESS_BLOCKED:l}=r(312),i=new n;function m(e){return i.get(e)}e.exports={proxy:function(e){let t=a.create(null);if(a.defineProperty(t,"closed",{get:function(){return e.closed}}),a.defineProperty(t,"close",{value:function(){return e.close()}}),a.defineProperty(t,"focus",{value:function(){return e.focus()}}),a.defineProperty(t,"postMessage",{value:function(t,r,a){return e.postMessage(t,r,a)}}),!i.has(e)){top.SNOW_WINDOW(e);let r=new s(t,{get:function(t,r){let a=o.get(t,r);if(o.has(t,r))return a;if(o.has(e,r))throw c(l,r,e);return a},set:function(){}});i.set(e,r)}return m(e)},getProxyByOpened:m,forEachOpened:function(e,t){for(let r of i.keys())e(r,t)}}},278:(e,t,r)=>{let{Object:a,slice:s,Function:o}=r(14),{proxy:n}=r(134);function c(e,t){let r=a.getOwnPropertyDescriptor(e[t].prototype,"window"),s=r.get;r.get=function(){return n(s.call(this))},a.defineProperty(e[t].prototype,"window",r)}e.exports=function(e){var t;e?.documentPictureInPicture?.requestWindow&&(e.documentPictureInPicture.requestWindow=(t=e.documentPictureInPicture.requestWindow,c(e,"DocumentPictureInPictureEvent"),c(e,"DocumentPictureInPicture"),async function(){let e=s(arguments),r=await o.prototype.apply.call(t,this,e);return r?n(r):null}))}},373:(e,t,r)=>{let a=r(228),{getFramesArray:s,shadows:o}=r(648),{Object:n,Function:c,isConnected:l}=r(14);function i(e){for(let t=0;t<o.length;t++){let r=o[t];(!e||l(r))&&a(s(r,!1))}}e.exports={hookShadowDOM:function(e){let t=n.getOwnPropertyDescriptor(e.Element.prototype,"attachShadow");t.configurable=t.writable=!0;let r=t.value;t.value=function(e){let t=c.prototype.call.call(r,this,e);return o.push(t),i(!0),t},n.defineProperty(e.Element.prototype,"attachShadow",t)},protectShadows:i}},294:(e,t,r)=>{let{trustedHTMLs:a}=r(648),{Object:s,Function:o}=r(14);e.exports=function(e){if(void 0===e.TrustedTypePolicy)return;let t=s.getOwnPropertyDescriptor(e.TrustedTypePolicy.prototype,"createHTML");t.configurable=t.writable=!0;let r=t.value;a.push(e.trustedTypes.emptyHTML),t.value=function(e,t){let s=o.prototype.call.call(r,this,e,t);return a.push(s),s},s.defineProperty(e.TrustedTypePolicy.prototype,"createHTML",t)}},716:(e,t,r)=>{let{Object:a,Array:s,getBlobFileType:o}=r(14),{error:n,ERR_BLOB_TYPE_BLOCKED:c}=r(312),l="KIND",i="TYPE",m="Blob",p="File",u="MediaSource",h=new s,g=new s("","text/javascript","text/css","application/javascript","application/css","image/jpeg","image/jpg","image/png","audio/ogg; codecs=opus","video/mp4","application/pdf","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");function d(e,t){return function(r,s){let n=new e(r,s);return a.defineProperty(n,l,{value:t}),t!==m&&t!==p||a.defineProperty(n,i,{value:o(n)}),h.push(n),n}}e.exports=function(e){(function(e){let t=e.URL.createObjectURL;a.defineProperty(e.URL,"createObjectURL",{value:function(e){return h.includes(e)&&function(e){let t=e[l];if(t===m||t===p){let r=e[i];if(!g.includes(r))throw n(c,e,t,r)}}(e),t(e)}})})(e),function(e){let t=e[p],r=d(t,p);function s(e,t){return r(e,t)}a.setPrototypeOf(t.prototype,s.prototype),a.setPrototypeOf(s.prototype,e[m].prototype),e[p]=s,a.defineProperty(t.prototype,"constructor",{value:s})}(e),function(e){let t=e[m],r=d(t,m);function s(e,t){return r(e,t)}a.setPrototypeOf(t.prototype,s.prototype),e[m]=s,a.defineProperty(t.prototype,"constructor",{value:s})}(e),function(e){let t=e[u],r=d(t,u);function s(e,t){return r(e,t)}a.setPrototypeOf(s,t),e[u]=s,a.defineProperty(t.prototype,"constructor",{value:s})}(e)}},648:(e,t,r)=>{let{tagName:a,nodeType:s,slice:o,Array:n,parse:c,stringify:l,Node:i,Document:m,DocumentFragment:p,Element:u,ShadowRoot:h,getContentWindow:g,getDefaultView:d,getOwnerDocument:b,stringToLowerCase:k,Object:y}=r(14),f=new n,j=new n;function w(e){return f.includes(e)}function v(e){if(w(e))return h;switch(s(e)){case i.prototype.DOCUMENT_NODE:return m;case i.prototype.DOCUMENT_FRAGMENT_NODE:return p;default:return u}}function x(e){let t=k(e);return"iframe"===t||"frame"===t||"object"===t||"embed"===t}function E(e){if(!e||"object"!=typeof e||s(e)!==u.prototype.ELEMENT_NODE||w(e))return null;let t=a(e);return x(t)?t:null}function T(e){return n.isArray(e)||(e=new n(e)),e}function O(e,t){let r=!1;for(let a=0;a<t.length;a++)e.includes(t[a])||(e.push(t[a]),r=!0);return r}e.exports={getDeclarativeShadows:function(e){return v(e).prototype.querySelectorAll.call(e,"template[shadowroot]")},makeDescriptorSetter:function(e,t){let r=y.create(null);return r.value=t,function(t){y.getOwnPropertyDescriptor(t,e)||y.defineProperty(t,e,r)}},toArray:T,isTagFramable:x,getOwnerWindowOfNode:function(e){return d(b(e))},getContentWindowOfFrame:function(e){return g(e,E(e))},getFramesArray:function(e,t){let r=new n;return null===e||"object"!=typeof e||j.includes(e)||!function(e){if(w(e))return!0;let t=s(e);return t===u.prototype.ELEMENT_NODE||t===u.prototype.DOCUMENT_FRAGMENT_NODE||t===u.prototype.DOCUMENT_NODE}(e)||(O(r,o(v(e).prototype.querySelectorAll.call(e,"iframe,frame,object,embed"))),t&&O(r,T(e))),r},getFrameTag:E,shadows:f,trustedHTMLs:j}},744:(e,t,r)=>{let{runInNewRealm:a}=r(407),{Map:s,toString:o,stringStartsWith:n,Blob:c}=r(14),l=new s,{createObjectURL:i,revokeObjectURL:m}=URL;e.exports=function(e){e.URL.revokeObjectURL=function(e){let t=l.get(e);return t&&(m(t),l.delete(t)),m(e)},function(e){let t=e.Worker;e.Worker=function(e,r){let s="string"==typeof e?e:o(e);return n(s,"blob")?new t(function(e){if(!l.has(e)){let t=`(function() { Object.defineProperty(URL, 'createObjectURL', { value: () => { throw new Error(\`
BLOCKED BY SNOW:
Creating URL objects is not allowed under Snow protection within Web Workers.
If this prevents your application from running correctly, please visit/report at https://github.com/LavaMoat/snow/pull/89#issuecomment-1589359673.
Learn more at https://github.com/LavaMoat/snow/pull/89\`) }}) }())

`+a(function(t){let r,a=new t.XMLHttpRequest;return a.open("GET",e,!1),a.onreadystatechange=function(){4===a.readyState&&200===a.status&&(r=a.responseText)},a.send(),r});l.set(e,i(new c([t],{type:"text/javascript"})))}return l.get(e)}(s),r):new t(s,r)}}(e)}}},n={};function c(e){var t=n[e];if(void 0!==t)return t.exports;var r=n[e]={exports:{}};return s[e](r,r.exports,c),r.exports}c.n=e=>{var t=e&&e.__esModule?()=>e.default:()=>e;return c.d(t,{a:t}),t},c.d=(e,t)=>{for(var r in t)c.o(t,r)&&!c.o(e,r)&&Object.defineProperty(e,r,{enumerable:!0,get:t[r]})},c.o=(e,t)=>Object.prototype.hasOwnProperty.call(e,t),t=c(352),r=c.n(t),Object.defineProperty(a=window,"SNOW",{value:function(t,r){e(t,r||a)}}),e=r(),a!==top&&(e=top.SNOW,a.SNOW(()=>{},a))})()}),c.push(e=>{!function(){let e=console.log.bind(console),t=!n.document;Object.defineProperty(n,"SCUTTLER",{value:(r,a)=>{t?a(r):n.SNOW(t=>{e("Snow detected a new realm creation attempt in MetaMask. Performing scuttling on new realm.",t),a(t)},r)}})}()}),Object.freeze(c),r.p="",(()=>{r.b=void 0!==o&&o.baseURI||n.location.href;var e={9121:0};r.f.j=(t,a)=>{var s=r.o(e,t)?e[t]:void 0;if(0!==s)if(s)a.push(s[2]);else if(9121!=t){var o=new Promise((r,a)=>s=e[t]=[r,a]);a.push(s[2]=o);var n=r.p+r.u(t),c=Error();r.l(n,a=>{if(r.o(e,t)&&(0!==(s=e[t])&&(e[t]=void 0),s)){var o=a&&("load"===a.type?"missing":a.type),n=a&&a.target&&a.target.src;c.message="Loading chunk "+t+` failed.
(`+o+": "+n+")",c.name="ChunkLoadError",c.type=o,c.request=n,s[1](c)}},"chunk-"+t,t)}else e[t]=0},r.O.j=t=>0===e[t];var t=(t,a)=>{var s,o,[n,c,l]=a,i=0;if(n.some(t=>0!==e[t])){for(s in c)r.o(c,s)&&(r.m[s]=c[s]);if(l)var m=l(r)}for(t&&t(a);i<n.length;i++)o=n[i],r.o(e,o)&&e[o]&&e[o][0](),e[o]=0;return r.O(m)},a=globalThis.webpackChunk=globalThis.webpackChunk||[];a.forEach(t.bind(null,0)),a.push=t.bind(null,a.push.bind(a))})(),(()=>{let e=Object.create(null);e.root="$root$",e.idmap=[["$root$",[100008,100073,100573,100900,102190,102320,102609,10264,102905,102985,103261,103321,103651,104231,104429,104728,104758,105049,1051,105214,105338,105522,105557,105653,105967,106828,106875,107230,107381,107580,107804,107874,107886,108116,108120,108178,108439,108474,108933,109312,109704,109889,110010,110303,110407,110814,110927,111644,111725,11188,111985,112021,112094,11253,112604,112652,113276,113337,113366,113848,114168,114174,114274,114533,115726,115809,115884,115960,116048,116255,116274,116372,116839,116882,117253,117455,117567,117580,11775,117903,117947,11795,118055,118190,118308,118670,118834,118997,119023,119278,119681,119789,120054,120209,120556,120572,120584,120693,120925,121216,121854,122175,122505,122536,123231,123391,123455,123556,12376,123784,123799,124397,124599,125091,125393,12569,125894,126142,126177,126370,126660,127015,127388,127565,127757,128364,128567,128715,130111,130331,130428,130723,130750,130780,130872,130920,13126,131666,13176,131811,132019,132476,132516,132693,13296,133195,133516,133598,133635,133714,133848,134236,134727,135047,135221,135362,135974,136088,136109,136426,136447,136862,137068,137557,137622,137627,137937,138409,138454,138623,138865,138915,139247,139284,139354,139668,139674,139833,139842,139976,14029,140580,140775,140778,141057,141573,141713,142014,14299,143195,143394,143472,143918,144586,144944,144988,145034,145102,145153,145502,145657,145738,145865,14600,146188,146194,146759,146802,146869,146888,147133,147278,147487,147599,148249,148496,148887,149040,149177,14919,149235,149235,149235,149235,149861,150350,150517,15151,15165,152256,152336,152411,15250,15289,153030,153059,153068,153294,153692,153738,153753,15392,154062,154565,154961,155180,155246,155429,155710,155862,156187,156540,156549,156721,156760,156852,156889,156955,157102,157234,157350,157395,15744,157479,157794,157944,157960,158175,158221,158259,158332,158374,158637,159163,15923,159307,159315,159472,159579,159673,159836,160087,160099,16026,160461,160628,160873,161356,161413,161863,162015,162444,162560,163305,163310,163611,163636,163723,163843,163993,16415,16467,164684,164983,16512,165139,165851,165937,165972,166133,166221,166532,166852,166879,167105,167134,167472,16750,167643,16809,168671,168798,16930,16961,169666,169727,16979,169889,17e4,170232,170237,170330,170455,170524,17079,170904,170951,171018,171229,171421,17198,172013,172153,172165,172806,173030,173319,173611,173674,174199,174520,174869,17513,175150,175436,175449,176022,176424,176570,176919,177348,177505,177540,177540,178096,178100,178121,17856,178665,178712,179113,179408,17967,179913,179946,180415,181231,181443,181726,181768,181921,182020,182321,182711,182721,182747,182824,18361,183876,184790,184899,185127,185164,185311,185331,185433,185458,185517,185615,185734,185878,186050,186186,186243,186339,186362,186417,186495,186644,186747,186943,187090,187306,188175,188189,188199,188221,189202,18921,189241,189332,189383,189389,189596,189620,189692,189726,189945,190032,19155,191557,192449,192832,193035,193055,193590,19374,193761,193945,193969,194175,194181,194351,194510,194735,195439,195603,195993,196051,196201,196358,196425,19684,197067,197362,197434,197434,197852,197875,197948,198339,19836,198444,198451,198588,198708,198717,198956,199238,199438,199448,199715,199861,200006,200058,200266,201044,201242,201249,201631,201686,201729,202064,202431,202561,202565,202929,203154,20317,203531,203619,204267,204283,20429,204325,204427,20450,204502,204582,205009,205009,205009,205009,205136,205756,205818,206252,206538,206841,206865,20760,208019,208234,208459,208566,208595,209062,209234,209284,210462,210509,210771,211157,211314,21211,212290,212528,212589,212814,212971,213406,213650,213751,214592,214597,215353,215612,216415,216729,217445,217702,217768,217768,217862,217865,21795,218033,218033,218033,218033,218033,21873,218743,218924,219115,21920,219336,219500,219661,220202,220313,220372,220464,220562,220566,220693,220893,221154,221349,221475,221526,221527,221628,221656,221677,222236,222260,222455,22249,222729,222779,22335,224052,224610,225087,225133,225761,225813,226183,226488,226535,226535,226535,226535,22677,227323,227406,227481,227600,227858,227894,22793,227980,228153,22831,228394,228677,228816,229326,229540,22958,229640,229880,2299,229976,230027,231638,231728,231769,232567,232611,232851,232937,23299,233001,233043,233479,233651,23471,23483,234852,234958,234959,235029,23560,235643,23565,235807,236123,236538,236622,236669,236940,237095,237106,237154,237219,237381,237587,237837,237997,238175,238304,238886,239128,239231,240066,240314,240497,240541,240735,240854,24094,241144,241759,241912,242100,242326,24296,243160,243176,243403,243549,24394,244174,244894,244970,245680,245749,245806,24609,246091,246683,247392,247404,247722,247755,247767,247924,247929,247938,24809,24831,248313,248463,248550,248866,249257,249957,250095,250286,25038,250594,250670,250862,25102,251087,251239,251457,251474,25183,251845,25221,252783,253042,253127,253529,253573,253628,253707,253814,254042,254467,254518,25456,254629,2547,254735,254890,255018,255301,25540,255544,255734,256080,256638,256718,256758,257429,257521,258380,25860,258833,259016,25905,259634,25990,260105,260184,260199,260677,260723,26133,261485,261523,261645,262279,262371,262541,262667,263022,26319,263294,263880,264013,264070,264198,264607,264727,266180,266391,266692,266892,266923,267208,267782,267935,268282,268405,268765,268804,269185,269243,269256,26956,269627,26973,270006,27057,270642,270671,270692,271077,271294,271326,271395,271525,271613,271641,271691,271912,27223,272342,272491,272721,27310,273136,273370,273404,273573,273978,27440,274584,274709,274796,275024,275059,275148,275577,276602,276629,276717,276814,277121,277315,277318,277336,277416,277933,278072,278332,278441,278457,278798,27906,279323,279623,28017,280560,280821,280838,280889,281351,281652,281753,281995,282078,282835,283003,283017,283042,28369,283875,284232,2844,284999,284999,284999,284999,285053,285063,28508,285133,285217,285412,285749,285770,286418,286434,286524,286545,286593,286831,286989,287838,287867,287961,288157,288166,288612,28872,288768,288827,288885,289036,28921,289341,289561,289614,289636,289750,2899,290185,290194,290254,290859,290944,291146,291319,291323,291680,2920,292106,292485,293217,293460,293941,294150,294151,29438,29472,294777,294935,294938,295282,295494,295627,29563,295704,295716,295857,296053,296260,29667,296780,297075,297214,297292,29800,298136,298191,298298,298457,298677,298789,299097,299150,299150,299165,299211,299316,299401,299539,29963,299871,300046,300047,300110,300425,300652,300652,300704,300833,301416,301622,302465,302579,302684,302764,302781,302876,302884,30294,303124,303374,303643,303646,303727,303879,304002,304473,304614,305739,306214,30642,306585,306639,306650,306814,306970,307039,307136,307201,307698,307890,308203,308206,30860,308734,309037,309114,309172,309281,30943,30943,30943,30943,309724,309750,309950,310311,310728,310867,311232,311441,311734,311734,311736,311925,31213,312332,31234,312584,312641,312680,312710,312757,312787,312902,31309,313400,313418,31342,313484,313535,313847,3139,314007,314793,314876,315282,315313,315697,316358,316864,317021,317095,317161,317194,317678,318443,318630,318768,318808,319381,319424,319838,319961,32002,320059,320337,32052,320821,320847,320889,321194,321505,321602,322064,322244,323131,323195,323291,323358,323673,324039,324143,324357,324457,324746,324784,32501,325135,325870,326089,326162,326325,326364,32637,326457,326563,32667,32667,32667,32667,327253,327342,327563,327731,328436,328746,328861,329345,329519,329904,329939,330242,330965,331134,331276,331351,331413,331651,331722,331822,332028,332203,332414,332427,332471,332647,332764,333188,333304,333332,333530,333592,334100,334111,334205,334265,334823,334836,334990,335,335267,335270,335517,335683,336576,336680,336795,336960,337208,337214,337720,337735,337736,338028,338184,338865,339169,33922,339566,339745,339829,34038,34045,340687,340737,34121,34125,341441,341595,341616,341695,3417,344531,344617,34474,344827,345297,345404,345661,345757,345791,345949,3460,346200,346375,346667,348264,348809,348826,348826,348826,348826,348826,34899,349028,349450,349465,349723,350241,35091,351309,351651,351794,351806,352136,352412,353140,353183,353531,353660,353735,354699,354779,355123,355816,355852,355933,356333,356743,357470,357594,357801,358254,358343,358623,35941,359807,35986,359902,361507,361705,361713,361734,362020,362254,362418,362705,362705,363175,363786,363910,364209,364289,36430,364679,364756,365161,365283,365337,365377,365521,365702,365919,366092,366456,366932,36696,367058,367149,367566,367611,367699,368656,368729,368872,368891,36915,36915,369436,369436,369436,369436,369920,370236,37083,371052,37192,372171,372363,37315,373177,373472,373492,373748,373824,373889,374064,37408,374190,374195,374470,374753,375074,375185,375262,37557,376012,376084,37615,376213,376906,377109,377163,377495,377558,377588,377652,377818,377946,378033,378036,378247,378335,37837,378442,378456,37855,378831,378831,37902,379049,379277,379531,379738,380127,380583,380855,381122,381315,381969,382043,382045,382583,383026,383046,383073,383145,383280,383687,384043,38439,38493,385028,385672,386019,386522,386645,386691,387131,387192,387651,38780,388064,388205,388296,388434,388511,388602,389097,389316,389461,38950,389610,389726,390049,390340,390764,390808,391032,391163,391327,391677,392107,392503,392667,392838,392968,39321,393384,393406,393695,393740,39377,393980,394579,394678,394749,394810,396132,396200,396602,396773,396944,397171,397361,397773,397937,398011,398278,398612,398778,398785,399151,399362,399431,399458,400566,401073,401085,401138,401379,401515,401607,401781,401864,401870,401981,402280,402735,403225,403416,403485,403526,403634,404186,404499,405272,405795,405970,406044,406515,406639,406861,407627,407711,408161,40926,409325,409629,409823,410006,410111,410716,41073,410931,410985,411290,411360,411419,411449,41189,411926,411930,411969,412522,41348,413661,413700,413881,4142,414410,414580,414744,414770,414774,41488,415051,41519,415221,415344,415506,41601,416305,41656,416817,41728,4186,418635,419277,419309,419362,41937,420151,420322,420736,420765,420990,421008,421046,421203,422113,422132,422607,422638,422760,422909,423262,423533,423694,42395,424068,424073,424075,424408,424727,424731,424898,425037,425123,425195,425348,425462,425784,42594,426021,426171,426195,426613,426639,426898,426939,427615,42768,428050,428217,42824,428484,428710,429120,429184,429758,429780,429864,429866,429891,430167,430560,430606,430679,430801,43089,430900,431218,431319,431423,431534,43186,431877,432121,432142,432155,432514,433285,433332,433462,434024,434062,434062,434062,434062,434268,434296,434306,434424,434663,434718,435e3,435025,435121,435210,435602,435671,435766,43588,435956,436199,436232,436821,436892,436954,437054,43710,437165,437173,437313,4374,437622,437628,438174,438376,438749,438797,438835,438839,439113,439117,439122,439281,439413,439728,439748,439786,439874,439984,440193,440369,440490,44061,440770,440776,440900,440952,440976,441,441308,44135,441670,441949,442100,442286,442722,442938,443068,443377,443634,443820,443900,444504,444837,445272,445274,445495,44585,446068,446084,446649,447104,447213,447238,447614,448138,448139,448350,4486,448849,449024,449367,449566,44970,450295,451041,451069,451083,451249,451368,4515,45181,451881,452288,452489,45251,452614,452797,45294,453450,453643,453688,454050,454091,454159,454293,454704,454735,454744,454810,45500,455478,455550,456364,456401,4565,456614,456641,4568,456825,456827,45779,457965,457972,458156,458261,458416,458417,458446,458544,458606,458981,459001,459396,459565,459766,459837,459940,459979,460258,460333,460383,46127,461297,461376,461386,461487,46152,46164,461720,462284,462893,463885,464183,464478,464865,465188,465243,465339,465594,466213,46639,466758,466808,46754,467648,467907,46847,468528,468871,469076,469134,469496,469885,469964,471326,471620,471641,472652,472961,473025,473064,473321,473377,473625,473673,473907,474185,474787,475112,475252,475274,475281,475304,475308,476353,476407,476637,476801,476857,477055,477082,477232,477479,477738,478367,478420,478976,479036,47913,479248,479271,479376,479447,479731,47987,480021,480031,480242,481108,481343,481382,481394,481654,481686,482118,482133,482442,482747,482903,482903,483388,483405,483596,483801,483831,483885,484157,484302,484332,48569,485870,486073,486840,487115,487135,487208,487429,48750,488326,488538,488674,488848,488862,489019,489060,489076,489220,489352,489876,490073,490288,490335,490565,491016,491047,491305,491359,491698,492061,492784,492949,4930,493059,493063,493070,493305,493332,493404,493816,49392,493999,494085,494142,494704,495019,495168,495389,495749,495946,495958,496017,496324,496775,496920,497023,497272,497305,497432,497825,497946,498387,498603,498624,498784,499749,499763,499985,500590,500635,500855,501047,501056,501100,50133,502459,502981,503157,503301,503344,503448,503843,504423,504507,504580,504622,50468,504714,504732,505071,50550,506484,506672,507003,507049,507096,507206,507321,507335,507475,507837,507922,508112,508115,50912,509289,509486,509855,510172,510353,510995,511037,511042,511265,511357,512203,512664,512755,513017,513258,513348,514218,514753,514800,514919,514981,515168,515405,515672,515923,516020,516776,516868,517186,517299,517452,517846,517899,518176,518307,518332,518684,518706,518805,518833,518992,519136,51953,519632,51966,519735,519740,520124,520143,520169,520418,520425,520803,520803,521112,521128,521276,521607,521640,521824,521981,52212,522317,522442,523162,523311,523315,523391,523414,523891,524313,524512,524670,525468,525721,52599,52600,526126,526194,527011,527122,527512,5281,528804,529,529023,52918,529244,529247,529480,529944,530189,530690,530868,530932,530953,530953,530980,531004,531325,531728,531888,532115,532203,532639,532690,532747,532878,532912,533132,5338,534115,534863,535177,535272,535411,53577,536006,536084,536112,536188,536266,536529,536827,536850,537127,537238,537610,538093,538218,538710,538874,539322,53987,5402,540603,540866,540993,541111,541255,541417,54160,541909,541984,542159,542386,542429,542492,542527,542565,542780,543007,543246,543427,543960,544187,544323,544813,544942,544952,545058,545149,545265,545423,545791,546219,546243,546800,547010,54724,547950,548631,548764,54883,549169,549700,549991,550141,55035,550795,550967,551044,551518,55273,552954,553038,553346,553607,553670,553827,554218,554376,554606,555426,555974,556079,556097,556109,556354,55638,556888,557023,557213,55742,55768,558203,558236,558726,559167,559289,559474,559855,559873,560094,560304,560670,560979,561012,561092,561864,562421,562429,562719,562945,563451,563632,563712,564039,564122,564260,564570,564993,565478,565654,565758,565861,566580,56675,566805,567064,567230,567637,568185,5685,568615,568648,568740,568893,569337,5696,5696,570330,570578,570601,57063,570702,571086,571371,571745,572107,572213,572318,572356,57260,572640,572738,57279,573139,573630,573713,573873,574013,574193,574211,574356,574618,575125,575214,575483,575510,57562,575774,57593,57605,576384,576693,576988,577205,577237,577279,577300,577576,577683,578173,578423,578926,579303,579847,580030,58017,580197,580253,580445,580585,580610,580752,580832,581207,581716,581831,581843,582304,582361,583053,583064,583078,583919,58401,584243,584358,585134,585453,585670,58568,585844,585928,586143,586229,586297,586297,586297,586297,58631,586577,586614,586651,586677,587,587028,587109,587279,587295,587569,588298,58836,588498,588575,588917,589022,58925,589562,589569,589628,589642,590151,590343,590446,590656,590909,590938,591049,591053,591058,591197,59121,591425,592181,592492,59293,592990,593130,593226,593258,593457,593767,594108,594450,594768,594794,595468,595502,59555,59555,595765,595799,595901,596271,596364,596396,596414,596472,596554,596786,596790,596829,596842,597106,597436,598480,598607,59862,598649,598667,598905,599e3,59904,599211,599224,59939,599425,599433,599645,599948,599962,60046,600540,600663,600831,600857,601504,60192,602532,602702,603343,603534,603735,603742,603880,604034,604239,604784,605565,60572,606122,60626,606308,606319,606481,606736,606760,606807,606965,607335,607702,607854,608182,608291,608416,608972,609043,609654,609949,609989,610332,610378,610696,610923,611770,6121,612650,61283,612903,613519,613545,614323,614547,614781,614821,614852,614855,615924,616212,616245,61625,616713,617209,617651,617936,618052,618277,618373,618693,618932,619232,619454,619470,619486,619745,62e4,620065,62037,620852,621358,621856,621902,622172,622713,622784,622922,622999,623236,623654,624250,624404,624720,625526,625546,625564,626041,626438,626481,626667,627009,627038,627375,627920,628367,628478,628530,628695,629265,629273,629456,629909,630496,630841,631275,631442,631672,6324,63260,632690,632894,633090,63342,63360,633683,633690,633723,633785,634120,634419,634521,634547,634730,635299,635349,635607,635876,636447,63681,63682,636925,636925,636925,636925,636968,637241,637247,637312,637330,637673,637720,637778,638063,638113,638228,638846,638927,638940,639049,639155,639362,639393,639498,639698,639898,64006,640421,640469,640469,640469,640469,640655,640758,640764,64099,641315,641316,641334,641762,64235,642350,642540,643246,644757,64478,644854,644907,644992,645930,645999,646178,646241,646289,646552,646826,647168,647635,647731,648210,648273,64858,648883,648954,648975,649071,649403,649564,649943,649994,650,65036,65068,650710,650836,650981,651095,651988,652119,652167,652318,652499,65262,65283,653069,653098,653176,654027,654352,654639,655204,655335,655746,655850,656054,656252,656270,656317,656615,656685,657027,657218,65725,65756,657624,657700,657754,658152,658268,658502,658506,658684,658718,658805,658924,65896,659119,659173,659195,659212,659579,659677,660063,660301,660955,661287,661377,661692,661796,662067,662090,662509,662664,66305,663185,663195,663870,66399,664933,665028,6651,665309,665541,665618,666011,666499,666766,666771,66681,667202,667436,667505,667551,66760,667629,667855,667911,66822,668673,668751,668795,668845,668852,6690,669165,669217,669378,669642,669909,670429,670478,67093,671054,671054,671075,671656,671839,672632,672911,673265,673907,673913,674061,674156,674382,674924,675274,67529,675318,675656,67606,676432,676525,67661,676864,677245,677431,677465,677890,678606,678742,678863,67957,679718,680094,680245,680440,680440,680573,680927,68102,681292,682428,682504,682566,682685,682705,682801,682988,683,68306,683061,683683,683996,684289,684835,684936,685555,685780,685986,686834,686898,686898,686898,686898,687165,687208,687209,687507,6877,68772,68806,68812,688355,688431,688713,68878,688843,68920,689786,689851,690109,690134,690554,691232,691241,691280,691284,691897,691901,692002,692322,69244,692464,692499,693124,693281,694068,694615,695094,695963,696054,696128,696439,696469,696778,697136,697141,697179,697363,697880,698208,698694,698891,699533,699755,700159,700823,700850,700898,701191,701728,70213,702176,70229,702294,702458,702802,703198,703279,703303,703346,703382,703885,704169,70435,704588,704901,705098,705106,705120,705195,705363,705406,705612,706229,706439,706890,706902,706990,707455,707502,707863,709085,70935,709723,709971,710100,7103,710335,710362,711023,711024,711055,711413,711457,71147,711540,711615,711994,712116,712177,712383,71239,712587,712894,713117,713317,713376,71353,713633,713700,71427,714725,714879,71507,715276,715386,715390,715863,715891,715918,716004,716229,716297,71707,717486,717504,718246,71826,719376,719928,72e3,720063,720262,720299,720578,720698,721127,7215,721755,72187,72196,722198,722361,72246,722513,72297,723496,723605,72417,724180,724194,724270,72435,724391,724593,724803,7249,724935,725018,725103,725115,725156,725411,725528,725613,725629,725736,725873,72617,726607,726999,727200,727300,727343,72828,728284,728497,728620,728857,728966,729671,729688,729866,730027,730280,730319,73050,730597,73095,730994,731047,731136,731409,731728,731929,732006,732121,732186,732257,732537,732546,732623,73338,733477,733679,733686,733814,734041,734221,734381,734845,734910,735191,735311,735641,73579,735929,736053,736170,736172,73628,736552,737117,737445,737513,737739,738,738012,738215,738455,738663,738903,738945,73899,739164,739354,739451,739472,739646,740366,740674,740764,740863,740953,740953,740953,740953,741070,741212,741231,742303,742448,742464,742673,74296,743098,743207,743241,743771,743890,744093,744239,744349,744850,745e3,745095,745332,745385,745565,745671,745766,746769,746828,747485,747598,747707,747835,748049,748222,748349,748364,748717,748792,748811,748994,749035,749153,749965,7500,750001,750291,751368,751490,751557,751741,751804,752271,752351,7533,753808,753872,753908,75433,754486,754720,755047,75514,755935,756036,756098,756497,756509,756733,75695,757011,757330,757559,757867,757923,758285,758363,758438,759027,75921,759595,759791,760264,760805,760831,760928,760994,761179,761649,76184,762048,762115,76216,762418,762430,762526,762550,762661,762780,763052,763073,76318,763220,763548,763639,763797,763985,764130,764141,764467,764477,764540,764670,764960,765124,765919,766116,766142,766204,766322,766372,766597,766707,767248,767283,767798,767807,767902,767946,768110,768132,768344,768388,768427,768466,768829,768968,769544,769604,769682,770100,770399,770418,770845,771042,771085,771201,771669,772294,772409,772638,772961,773318,773417,773703,773990,774153,774243,774281,774501,774643,775072,775092,775150,775458,776141,776320,776323,776500,776598,77691,777006,777040,777051,777544,777544,777732,778063,778093,778368,779370,779476,779719,779865,78052,780555,780578,780671,780829,780991,781342,781448,7815,781654,782113,782189,782219,782343,782399,782747,782895,783026,783058,783063,783169,783431,783566,783574,783714,78400,784108,784179,784289,784402,784598,784671,784686,785015,78513,785449,785591,785859,785935,786688,786748,786814,786881,78714,787544,787561,787631,78766,787719,788152,788175,788289,788614,788787,788932,789006,789151,789763,790394,790453,790804,790882,791774,791791,791796,79194,79222,792570,792706,793174,793574,793591,793735,793923,793997,794360,79443,794646,794857,794921,795223,796110,796178,796213,796213,796404,796404,796404,796404,796404,796407,796474,797056,797095,797300,797948,798328,798422,79865,798806,798844,799580,799846,800014,800609,801121,801189,80127,801516,80157,801689,802184,8024,802870,80296,80321,80339,803402,804154,805326,805626,80583,805921,806084,806201,806625,806911,806987,807424,807605,80769,807720,807895,808069,808227,808576,808681,809120,80931,809581,809654,809726,809745,809873,810437,810462,810649,810814,810839,810964,811077,811437,811491,81170,811940,812045,812095,812553,812582,812667,812776,812994,813278,813321,813498,813897,813908,813939,814086,814393,815108,815126,81523,815268,815358,815479,815583,815614,815629,815841,815953,81598,816245,816402,816402,816402,816402,816467,816519,816752,818658,818798,818881,818906,81892,819157,819219,820311,820736,820831,820949,821136,821328,821436,821604,821781,821858,821931,822376,82353,823640,823673,823803,823803,824017,82405,824240,824781,825057,825066,825133,825267,825361,825461,825617,825745,826042,826300,826305,826596,826674,826686,826876,827013,827368,827370,827460,828126,828305,828787,829108,82911,829140,829272,829627,829751,829802,83014,830377,830636,830654,830755,830914,831125,831329,83149,831553,831703,832065,832430,832514,832670,832678,833342,833621,834018,83432,834923,835391,83555,835729,836293,836401,836441,836658,83679,837112,837287,8375,837731,837844,83819,838269,838517,838560,839975,840374,840483,841103,841130,841612,841759,841793,841860,841914,841929,841993,842004,842283,842658,84274,842856,844418,8456,845806,846442,846589,846973,84701,847258,847566,847681,847993,84849,84852,848587,848843,84886,848896,848896,849177,84944,849443,84955,850089,850891,850926,851365,851389,851711,851887,851987,852991,853249,853619,853927,854029,854110,854269,854353,854598,854700,854912,855451,855637,855769,856034,857172,857243,857665,858032,858067,858323,858493,858572,858621,858753,858863,858909,85892,858928,859504,85965,859689,859830,859915,860007,860339,860603,861029,86111,861710,862262,862760,863294,863339,863373,863459,863470,863566,86428,864348,864451,864468,865137,865210,865505,865797,865985,866262,866621,866625,86664,866708,866766,86678,866900,866910,866991,867458,868143,868415,868418,86907,86965,869782,869949,869949,870087,870445,870480,870543,870580,870721,871008,871008,871251,871895,87191,872200,872582,873084,87314,8737,873702,874029,874088,87488,875258,875450,875532,876032,876488,876747,87796,878066,878202,878208,878585,878638,878652,878875,879271,879429,879958,87998,880009,88014,880233,880273,880332,880416,880687,880724,88087,880909,880933,881061,881245,881882,882016,882298,882409,88247,882584,882597,882921,882978,88320,883682,883775,883931,885175,885276,885711,885830,886067,886125,886363,886376,886418,886418,886705,887281,887590,887717,888319,888867,88905,889767,88978,889814,890051,890154,890194,890491,890944,891545,891732,891765,892014,892267,892800,89340,893476,893638,894123,894193,894521,894521,894521,894521,894521,894873,894949,89507,895175,895280,895462,896090,896336,896559,896832,89724,897360,897654,898537,898837,899184,899210,899497,899869,900,90004,900106,900186,900311,900463,901497,901506,901773,901903,90260,902635,902820,90301,90317,9038,904196,904247,904249,904346,904438,904445,904466,904497,904555,904573,904678,90507,905366,905687,906057,906153,906283,906309,906588,906665,906980,907109,907569,907606,907631,908199,908226,908355,908717,908734,909122,909344,909381,909478,909506,909521,909582,909904,910413,91050,910606,910626,910689,910919,910940,911131,911134,911361,911455,911485,911552,911873,912047,912231,9123,912445,91245,91348,913620,913702,914022,914125,914431,914475,91448,914515,914665,914703,914826,914827,914853,914878,915363,915579,915742,915785,915925,916174,916272,916379,916398,916595,916824,916926,917073,917214,917429,918227,918540,918726,918739,918935,919074,91909,919388,91994,920006,920038,920117,920122,920342,920427,920499,920540,920623,921141,921828,921836,9220,922047,922347,922394,922549,922749,92326,923286,923381,923484,923682,923956,924056,924066,92491,92513,925153,92531,92532,92564,925942,926266,92627,926412,926745,926791,926912,927166,927379,927512,927737,92786,928062,92807,928404,928780,929343,929354,929366,929371,92984,92988,930171,930353,930574,930626,931025,931352,931507,932542,932586,932791,933330,933520,934011,934066,934381,934424,934460,934623,934644,934812,934899,935276,93534,935603,935614,935892,936007,936112,936276,936389,936431,936854,937237,937380,937403,937510,93769,937746,938247,938591,938685,938742,939195,939284,939679,93990,940337,940962,941311,941503,941581,942236,942566,942895,943202,943297,943398,943804,943819,943912,943971,944348,94448,944661,944674,944833,944976,945513,945519,946235,946251,94630,946502,946554,946802,947082,947162,947216,947266,947276,947290,948362,948569,948726,948835,949320,950230,950544,950659,950709,950852,950887,950913,9510,9510,9510,9510,9510,951508,951571,95180,951903,951998,952099,952409,953118,953215,953449,954280,954349,954376,954614,954726,954870,955414,955706,955944,956166,956517,956853,956861,957449,957604,957854,957948,958695,958709,95949,959517,959519,959588,959614,960085,960117,960178,960315,960929,961214,96146,962331,962416,962464,962474,962857,962986,963096,963266,963493,963866,964451,964779,96537,965519,965639,965657,966383,967142,967746,967746,968055,968255,968559,968565,969124,969210,969210,969402,969617,969716,969898,969917,970043,970276,970945,970962,971301,972160,972238,972380,972866,972896,972962,973629,973802,974209,974280,97441,974415,974535,974672,975269,975908,976809,976907,97695,977064,97719,977222,977378,97740,97813,978512,978969,979303,979536,97966,980062,98035,980385,9805,980632,981344,981834,981909,982287,982336,982587,982773,982928,983375,983556,983736,983821,983916,984409,984423,984679,985130,985544,985728,986693,98703,987181,987462,987606,987701,988110,988368,988600,988876,989288,989433,990087,990105,99027,990285,990295,990790,990970,991074,991625,991697,991718,992332,992377,992396,992565,992582,99301,993051,993164,9943,994682,994864,99490,99500,995477,995629,9957,99643,996526,996697,996788,997100,997222,997403,997595,997783,998025,998125,998797,99881,998879,999077,999156,999394,99981]],["@babel/runtime",[124255,127119,138312,140039,146436,228937,266103,325057,32990,34276,369953,387539,406527,431951,440484,449859,451055,45735,457812,463565,474658,487263,498421,500069,502349,505660,532895,560458,560901,562954,597347,612823,6490,656227,688947,709371,711646,71586,753341,757709,762014,779786,783093,800928,810356,824076,841024,854717,871820,877159,896478,91796,93072,935191,952165,979245,98105,991026,999227]],["@blockaid/ppom_release",[89962,96043]],["@emotion/react",[230908,954541]],["@emotion/react>@emotion/cache",[145319]],["@emotion/react>@emotion/cache>@emotion/memoize",[880657]],["@emotion/react>@emotion/cache>@emotion/sheet",[849159]],["@emotion/react>@emotion/cache>stylis",[176154,272480,292907,709823,857267,985114]],["@emotion/react>@emotion/serialize",[612093]],["@emotion/react>@emotion/serialize>@emotion/hash",[866385]],["@emotion/react>@emotion/serialize>@emotion/unitless",[591217]],["@emotion/react>@emotion/use-insertion-effect-with-fallbacks",[128999]],["@emotion/react>@emotion/utils",[839145]],["@emotion/styled",[266708,551187]],["@emotion/styled>@emotion/is-prop-valid",[262835]],["@ensdomains/content-hash",[356437,451783,687154]],["@ensdomains/content-hash>cids",[584728,707215]],["@ensdomains/content-hash>cids>multibase",[514284,535426,563455,721316,840247]],["@ensdomains/content-hash>cids>multibase>@multiformats/base-x",[362219]],["@ensdomains/content-hash>cids>multihashes",[215067,508380]],["@ensdomains/content-hash>cids>multihashes>uint8arrays",[689713,816796,870659]],["@ensdomains/content-hash>cids>multihashes>varint",[172319,215425,642209,882867]],["@ensdomains/content-hash>cids>uint8arrays",[205516,357568,868615]],["@ensdomains/content-hash>js-base64",[461462]],["@ensdomains/content-hash>multicodec",[454260,475676,558519,588582]],["@ensdomains/content-hash>multicodec>uint8arrays",[27360,383281,402713,46652,811595,812563]],["@ensdomains/content-hash>multihashes",[941633,942494]],["@ensdomains/content-hash>multihashes>buffer",[117552]],["@ensdomains/content-hash>multihashes>multibase",[284650,300094,512424,518529,816561]],["@ensdomains/content-hash>multihashes>multibase>base-x",[628251,874484]],["@ensdomains/content-hash>multihashes>varint",[262278,490408,643732,755064]],["@ensdomains/content-hash>multihashes>web-encoding",[193574]],["@ethereumjs/tx",[100452,11213,126896,127314,127469,1546,155e3,18559,215366,242676,26581,279528,282703,325733,34514,362706,369284,373475,407539,419035,443901,460714,56061,571637,579062,584390,673015,732013,792400,815357,821621,830723,986319,988296]],["@ethereumjs/tx>@ethereumjs/common",[12150,138049,177717,207769,246417,301776,379396,428097,440598,507665,617778,636873,731571,77547,921628,932733]],["@ethereumjs/tx>@ethereumjs/rlp",[626536,738130,971047]],["@ethereumjs/tx>@ethereumjs/util",[110418,160942,173930,18546,197133,198965,199456,206296,211645,262336,29433,296648,310188,314507,32394,336422,341872,349456,384377,388655,399909,416527,437881,44355,448578,478459,47909,481986,49107,516864,543178,54798,580203,586720,596187,605645,632496,657076,671762,741736,743151,783798,81010,83895,855224,874349,881019,888838,890415,892667,894563,898069,899217,906238,925263,932477,944516,949237,99683]],["@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography",[110377,219828,287361,291166,301302,401868,452197,535309,567417,687760,732]],["@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/curves",[107004,108099,162209,224981,238315,266786,278956,47822,495448,568478,617072,622643,671003,678298,710609,762871,778004,79210,796262]],["@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/hashes",[10780,17401,224683,285861,321705,359750,445115,447856,476244,481449,511241,533968,543657,582179,610068,625500,792721,813303,915253,926645,929920,945026,963426,969910]],["@ethereumjs/tx>ethereum-cryptography",[271465,377217,775440,81446]],["@ethereumjs/tx>ethereum-cryptography>@noble/hashes",[130407,224661,228143,362180,532953,742134,74869,960329]],["@ethersproject/abi",[105312,173862,207619,2720,275648,283353,290117,295467,363328,380106,393718,395068,402741,403119,40473,408505,450337,460704,485050,520234,552281,552364,60548,611782,629915,651911,715904,81505,849027,871050,923263,928097]],["@ethersproject/bignumber",[234740,323489,367302,532192,631229,657036,726731]],["@ethersproject/bytes",[198589,524443,977952,993558]],["@ethersproject/contracts",[264926,295523,790916,838617]],["@ethersproject/hdnode",[413049,42014,49182,563965]],["@ethersproject/providers",[128840,144240,203284,213037,235086,243681,26301,272585,286156,288881,31,345834,375693,380392,386903,396515,404593,416895,440652,451241,48080,504409,613248,675682,683411,698803,700531,702541,728024,73094,732500,806355,819790,861302,873437,916802,930847,935424,937786,981328]],["@ethersproject/providers>bech32",[399580,579841]],["@ethersproject/transactions",[387833,46308,482925,894e3]],["@fortawesome/fontawesome-free",[1527,1527,1527,1527,411525,411525,411525,411525,70035,70035,70035,70035]],["@google/genai>protobufjs",[119463,138217,151942,173310,179394,19298,218825,233393,23346,265120,275867,277049,28e3,281537,299467,305297,306722,31787,319347,350553,351947,35271,363917,391222,411124,424830,440818,462229,481277,488703,506830,507776,540186,54984,550602,566535,592094,599071,615815,626081,643600,649399,677694,682188,720035,730044,761437,762632,792509,798400,798572,807996,817362,818306,829594,85127,864122,923043,929078,956568,960613,961051,96183,971709]],["@google/genai>protobufjs>@protobufjs/aspromise",[28178,35757]],["@google/genai>protobufjs>@protobufjs/base64",[16754,380567]],["@google/genai>protobufjs>@protobufjs/codegen",[675374,80225]],["@google/genai>protobufjs>@protobufjs/eventemitter",[846230,855605]],["@google/genai>protobufjs>@protobufjs/fetch",[29691,873489,890554,895260]],["@google/genai>protobufjs>@protobufjs/float",[179442,328223]],["@google/genai>protobufjs>@protobufjs/path",[437271,628850]],["@google/genai>protobufjs>@protobufjs/pool",[476366,725269]],["@google/genai>protobufjs>@protobufjs/utf8",[843255,966234]],["@google/genai>protobufjs>long",[223361,35849]],["@keystonehq/bc-ur-registry-eth",[2593,544829]],["@keystonehq/bc-ur-registry-eth>@keystonehq/bc-ur-registry",[124e3,191052,231626,249615,265655,2977,459024,467722,527355,534855,564315,573995,57636,646539,67798,682001,747747,773884,794735,804119,867283,883483,927029,939286,976399,987339]],["@lavamoat/lavadome-react",[494708]],["@lavamoat/webpack>json-stable-stringify>isarray",[664074,841407]],["@lavamoat/webpack>json-stable-stringify>object-keys",[109346,1314,266165,69051,910229,959646]],["@ledgerhq/errors",[30649,315100,419422,964081]],["@ledgerhq/hw-app-eth",[104027,104586,113800,268879,30606,383317,463313,536227,551257,568746,63684,687439,705565,906779]],["@ledgerhq/hw-app-eth>@ledgerhq/cryptoassets-evm-signatures",[116736,116736,124859,124859,163015,163015,169781,169781,199597,199597,210703,210703,230970,236883,236883,248848,248848,250685,250685,255154,255154,258052,258052,274109,274109,322847,322847,334270,334270,347020,347020,366551,366551,369002,37908,37908,384717,384717,404282,404282,416093,416093,419682,419682,443852,443852,462622,462622,477649,477649,480075,480075,518851,518851,519988,519988,524815,524815,527390,527390,545688,545688,579237,579237,590888,590888,591272,591272,594750,594750,605933,605933,610625,610625,616814,616814,626884,626884,668059,668059,672311,672311,67928,67928,696055,696055,730571,730571,743225,743225,745686,745686,762051,762051,765119,78373,78373,787985,787985,819889,819889,835776,835776,848707,848707,867849,867849,89350,89350,895421,895421,902902,902902,908299,908299,9231,9231,938612,938612,950401,950401,95776,95776,983883,983883]],["@ledgerhq/hw-app-eth>@ledgerhq/domain-service",[224675,565967,862553]],["@ledgerhq/hw-app-eth>@ledgerhq/evm-tools",[454077,819304,977702]],["@ledgerhq/hw-app-eth>@ledgerhq/evm-tools>@ledgerhq/live-env",[265370,373941]],["@ledgerhq/hw-app-eth>@ledgerhq/logs",[137921,878528]],["@ledgerhq/hw-app-eth>bignumber.js",[784124]],["@ledgerhq/hw-transport",[469552]],["@ledgerhq/hw-transport-webhid",[53406]],["@ledgerhq/hw-transport-webhid>@ledgerhq/devices",[42324,695006]],["@ledgerhq/hw-transport-webhid>@ledgerhq/devices>semver",[122508,124306,153063,156827,196336,206080,219259,238402,248308,254004,273435,281017,2911,292487,308262,327803,35765,375822,421895,48037,486088,50122,5166,599021,632189,66184,723811,734082,744484,756398,762961,81032,829019,832090,852453,853846,867350,898423,898721,901711,909957,93192,960393,989346,997168]],["@ledgerhq/hw-transport-webhid>@ledgerhq/hw-transport",[127439]],["@metamask/abi-utils",[104527,188300,191844,205067,212005,252332,287633,29607,299205,311312,321138,34475,367419,458081,479238,502414,532046,548249,553588,558282,601499,620595,627674,637609,666335,713501,743732,755921,756330,785400,833750,838797,867055,936392,939255,961858,968912,974538,985810,986563]],["@metamask/account-api",[153586,321829,360726,384170,462357,474907,529498,531819,674288,689812,716904,809904,809910,974800]],["@metamask/account-tree-controller",[122341,175270,187952,212369,216591,270718,293239,294987,321902,335349,349391,370246,384983,393349,402561,408041,41997,422719,424752,436829,451446,460699,517113,524339,550321,564758,564855,574357,599500,606160,636453,662092,6814,687542,734827,758496,788527,796463,816987,81909,827362,873836,885713,93043,931609,97640,981064,98970,992452,993561]],["@metamask/accounts-controller",[454359,529068,53178,987279]],["@metamask/accounts-controller>ethereum-cryptography",[264592,586390,612662,671508]],["@metamask/accounts-controller>ethereum-cryptography>@noble/hashes",[292769,407105,629163,653288,655163,700931,724563,872574]],["@metamask/address-book-controller",[719194]],["@metamask/analytics-controller",[118105,266863,43509,998404]],["@metamask/announcement-controller",[540917]],["@metamask/approval-controller",[153453,241917,394813,65997]],["@metamask/assets-controller",[143147,147759,163545,168256,168359,169086,182088,19837,200649,241943,253139,26522,266468,267269,269575,279549,285684,286306,286672,340969,347263,349843,350266,370534,371528,374360,37479,390130,391638,405369,44327,496414,500016,502199,50327,506990,514773,528304,532612,535325,548733,583584,603342,615137,618295,631549,641245,646318,64906,659933,685951,711103,745908,747837,754049,777393,78089,810628,811752,820927,833870,860645,889133,912395,913292,913517,91937,935223,94977,96830,968666,96869,979117,983918,989832]],["@metamask/assets-controller>bignumber.js",[694204,963294]],["@metamask/assets-controller>p-limit",[336741,451646]],["@metamask/assets-controller>p-limit>yocto-queue",[632773,951874]],["@metamask/assets-controllers",[155938,158708,227462,232858,252816,269791,314747,337947,348157,383559,399475,44406,455121,469521,469817,47056,473404,496218,504120,51554,518779,525289,527184,558774,602744,625436,629210,633591,642744,650464,693674,694863,698513,75857,76667,798082,80576,811220,828388,855536,881017,885680,963666,987378,99926]],["@metamask/assets-controllers>@metamask/abi-utils",[110978,379982,40400,410782,460080,532064,574295,653800,665897,760370,762042,79244,842351,843075,843852,927643,934351,978932,983414,989813]],["@metamask/assets-controllers>@metamask/abi-utils>@metamask/utils",[152946,335160,382352,403644,443005,443526,486520,524429,602405,67236,672573,760297,82434,835140,861840,86584,876007,957598,980828,984122,990402]],["@metamask/assets-controllers>@tanstack/query-core",[121249,153573,183262,241857,341838,353808,39599,434787,511481,530337,611122,670839,688796,709469,974298]],["@metamask/assets-controllers>multiformats",[102959,137398,164284,2180,255843,272323,367504,371330,393293,415178,421247,526898,558696,603409,617877,62677,64844,649495,650504,6659,694756,748102,796271,814198,815982,81894,861651,86192,935420,945202,959605,963547,981279]],["@metamask/assets-controllers>single-call-balance-checker-abi",[523973,800904]],["@metamask/authenticated-user-storage",[366552,512604,735650,796568]],["@metamask/base-controller",[100209,100209,293889,293889,401593,418920,418920,552558,552558,811690]],["@metamask/bitcoin-wallet-snap",[886357]],["@metamask/bitcoin-wallet-standard",[243229,337874,467743,500285,63130,747555,776179,789365,880287,884948,921950,985447]],["@metamask/bitcoin-wallet-standard>@exodus/bitcoin-wallet-standard>@exodus/bitcoin-wallet-standard-core>@exodus/bitcoin-wallet-standard-chains",[467062]],["@metamask/bitcoin-wallet-standard>@exodus/bitcoin-wallet-standard>@exodus/bitcoin-wallet-standard-core>@exodus/bitcoin-wallet-standard-features",[157519]],["@metamask/bitcoin-wallet-standard>@wallet-standard/wallet",[491867,856492]],["@metamask/bridge-controller",[10669,166876,173624,175070,182317,182332,182348,197267,19733,203612,213142,214230,218494,229718,243074,248406,26424,269405,282570,324133,383442,394184,402914,404283,408516,408776,436243,440534,474207,475583,487592,511992,527398,527704,550293,563197,584207,589788,599076,614223,619489,641650,66216,663872,688326,709096,748512,76538,793110,839517,864103,908029,91008,912763,917425,930221]],["@metamask/bridge-controller>bignumber.js",[502770,990088]],["@metamask/bridge-status-controller",[156424,226352,230491,239596,249289,250217,277373,283379,359698,402891,457684,459772,549320,563764,564367,564583,581457,593922,602225,634723,651356,657950,662620,666379,703316,740984,76114,765681,822011,822177,82763,851583,913379,930168,935704,937444,956997]],["@metamask/bridge-status-controller>bignumber.js",[23339]],["@metamask/browser-passworder",[814320]],["@metamask/chain-agnostic-permission",[139341,145096,155749,156479,198095,296639,381375,444501,626630,728810,745814,746723,77523,787218,816634,825365,846671,849231,85904,862259,8655]],["@metamask/chain-agnostic-permission>@metamask/api-specs",[173810,212257,751601,892406,934683,934683,934683,934683,934683,99790,99790,99790,99790,99790]],["@metamask/claims-controller",[330808,36693,3824,515813,724617,921469]],["@metamask/claims-controller>@metamask/controller-utils",[337098,397155,498606,596979,778386]],["@metamask/client-controller",[23088,599726,911765]],["@metamask/compliance-controller",[332771,361978,713765,832380,904773,955947]],["@metamask/config-registry-controller",[443736,771948,874140]],["@metamask/connectivity-controller",[110931,304893,440931]],["@metamask/contract-metadata",[130541,238366,243179,243179,243179,243179,243179]],["@metamask/controller-utils",[17605,217912,30018,331489,395771,465709,496705,51664,644174,657638,672307,683410,725088,790580]],["@metamask/controller-utils>@metamask/eth-query",[404176,605895]],["@metamask/controller-utils>@metamask/ethjs-unit",[797809,886634]],["@metamask/controller-utils>@metamask/ethjs-unit>@metamask/number-to-bn",[360646,611538]],["@metamask/controller-utils>@spruceid/siwe-parser",[100020,129409,751528,827111,890577,955286]],["@metamask/controller-utils>@spruceid/siwe-parser>apg-js",[118675,119008,1305,133543,135322,14699,151097,190686,204777,216202,245981,283691,383737,388091,388682,397251,397721,40754,431304,442480,46509,469328,47036,488665,496562,506465,537939,548907,555014,557404,622282,649272,670078,720843,736427,74176,77118,771733,778263,810722,820724,862316,872735,88738,90040,939116,965892,980349]],["@metamask/controller-utils>@spruceid/siwe-parser>valid-url",[221490]],["@metamask/core-backend",[118914,129697,209656,234697,396880,440116,476069,52275,562425,64637,736094,852281,926115,943334,947988,955781,994506]],["@metamask/core-backend>@tanstack/query-core",[139151,183364,191522,194019,229461,232318,239927,254562,277754,322615,400632,480615,483152,490130,516528,539820,555558,576455,598622,617226,721039,740812,759119,790381,809633,834416,835468,888429,914435,962308]],["@metamask/delegation-controller",[299338,563262,718255]],["@metamask/delegation-controller>@metamask/keyring-controller",[227808,65016,948548]],["@metamask/delegation-core",[472678,846404]],["@metamask/delegation-deployments",[94993]],["@metamask/design-system-react",[100791,101545,104095,108379,111700,112038,112120,116791,118991,124856,126134,126528,139911,146950,147602,148696,153108,153472,154468,157783,157994,158250,158317,160370,160687,166537,168743,170533,173556,174795,17635,179218,180219,180781,181657,181902,183745,185194,186304,192794,195120,197951,201718,205278,212504,21263,21292,216346,216793,21875,219384,221371,222496,223901,227485,237405,237457,241686,243877,244569,244701,248477,250778,254465,255145,261181,266965,268870,27150,274207,2762,281051,281244,282311,283931,287002,287721,289055,290070,290605,296263,302175,303362,305955,306392,309111,310583,311698,314356,314756,323966,327468,330793,331498,33539,3372,339262,340390,343043,344809,346414,34997,353187,353438,355670,35721,364588,367792,376193,380917,381150,382707,385780,386745,38914,392800,395528,398412,40106,405165,407554,407699,409644,410701,411275,412524,424341,424502,431037,432914,434186,435684,437840,439295,439550,443273,445973,446947,449341,449565,450435,451902,452304,452668,454831,455836,457302,458646,459182,460390,465560,466770,47233,479746,480116,486359,48845,488581,492670,493611,49421,494800,498658,498677,502676,50627,507803,508323,508533,510243,516438,518206,518491,519559,520430,524405,526447,527442,529775,531462,533632,534408,53669,53784,538324,539783,540463,541292,544020,544944,546947,559099,563376,564250,566707,568085,576040,578429,579952,581745,582814,588106,588156,592479,593902,596940,600838,60209,602435,608887,60938,609415,616203,618485,621719,622832,623197,627871,632419,633400,634850,635860,639263,640713,641816,644493,65093,652230,655301,657580,65874,661447,671492,672992,67493,675319,676513,679085,679968,68323,68593,687513,687949,68940,690034,694394,709071,712964,719082,720483,72180,723576,729079,738935,742351,746005,746150,746812,748507,75451,756741,757654,758832,759310,762644,772737,773742,775075,779749,783088,783173,785016,785427,78990,790558,793216,797460,799163,804968,805600,806198,80649,81120,811571,814520,823445,827933,828116,829471,831404,832190,836726,838175,838490,842111,844326,845022,845417,848365,848558,849803,852336,853169,855034,865740,86660,866927,868118,870677,87288,874176,876365,877291,879575,879638,884056,890954,895370,903273,904306,907319,912629,913802,913807,922726,926968,927951,931231,93278,934509,935664,937069,938132,942959,949098,955662,958152,962428,963245,964414,966455,966872,970443,972938,976849,982635,983857,985268,990900,992164,995163,998246]],["@metamask/design-system-react>@radix-ui/react-slot",[700694]],["@metamask/design-system-react>@radix-ui/react-slot>@radix-ui/react-compose-refs",[128659]],["@metamask/design-system-react>blo",[150609,749193,904710,999084]],["@metamask/design-system-react>tailwind-merge",[704044]],["@metamask/design-system-shared",[206576,305142,506410,520858,556734,568894,584942,683772,706794,73804,75734,789292,79038,833304,848574,918070,918318]],["@metamask/design-tokens",[150197,158967,167203,18657,225344,236763,274241,288228,347861,354226,377043,394478,416063,43562,451587,456111,4796,482988,500944,520522,522686,528328,57071,580960,592338,633612,681561,681886,690691,711582,733721,759766,783158,784672,83024,831424,838442,857446,868103,870912,875644,912067,914025,91504,92071,932782,941630,972017]],["@metamask/eip-5792-middleware",[15722,157520,226158,493678,566799,601902,756243,829199,963674]],["@metamask/eip-5792-middleware>@metamask/transaction-controller",[348777]],["@metamask/eip-7702-internal-rpc-middleware",[10715,132291,295595,318343,676991]],["@metamask/ens-controller",[367577]],["@metamask/ens-resolver-snap",[764550]],["@metamask/eth-hd-keyring",[152791,205942,739583,780268]],["@metamask/eth-hd-keyring>ethereum-cryptography",[342271,731631,739412,780922]],["@metamask/eth-hd-keyring>ethereum-cryptography>@noble/curves",[182506,187339,257179,275501,354273,392145,511521,803300,862530,86744,87749,987385]],["@metamask/eth-hd-keyring>ethereum-cryptography>@noble/hashes",[109800,147274,185198,248241,361060,414585,455150,459303,474660,527563,536710,546308,591967,592843,612378,628989,701194,749245,792524,842060]],["@metamask/eth-hd-keyring>ethereum-cryptography>@scure/bip32",[483953,66889]],["@metamask/eth-hd-keyring>ethereum-cryptography>@scure/bip32>@scure/base",[46154,907904]],["@metamask/eth-json-rpc-filters",[117104,166189,286386,546759,573696,757918,790498,939862,992949]],["@metamask/eth-json-rpc-middleware",[112281,121009,14889,189713,197542,247270,313439,360458,367359,368847,400071,4275,430431,454375,576704,581722,585259,629507,641076,681384,706620,729132,8462,852692,865707,878843,881809,910743,936027,957027,962778,980845]],["@metamask/eth-json-rpc-middleware>safe-stable-stringify",[269593,330764,584294,612980]],["@metamask/eth-json-rpc-provider",[449129,55711,566247,884465]],["@metamask/eth-ledger-bridge-keyring",[238152,408424,638646,64822,712450,760785,77378,916461]],["@metamask/eth-qr-keyring",[234485,806955,807147,961658,985537,995456]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth",[11448,45117,545448,593961]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util",[106166,145273,168567,184430,208833,209107,218868,242063,260913,287160,317236,344007,365684,392833,413456,416838,439612,447377,451854,463212,499760,587542,650359,748299,761087,771662,819879,910697,924906,977461]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>@ethereumjs/rlp",[427158,506783]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography",[613096,64855,748037,765773,837272,908046]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography>@noble/curves",[109372,158115,197653,23489,291818,30493,388218,397454,774223,803659,854064,889447,933636,959172]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography>@noble/hashes",[101525,245326,274209,377027,402728,408688,545235,562204,671835,772775,778756,824280,860498,923857,953679,996388]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@keystonehq/bc-ur-registry",[115358,122720,133557,161856,177355,182666,22739,261574,297008,300971,311425,337251,337695,366027,399949,456406,461683,470297,470600,496447,500906,525856,547987,550736,555919,624951,638779,648167,67503,675722,700095,71375,738274,746060,749247,76268,782172,791890,807629,815607,816816,85578,879846,887673,906622,909710,93215,934292,949592,961101,99602,996720]],["@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>uuid",[125928,186669,241376,242547,255195,260475,301443,301766,33238,39135,419314,506592,544660,550868,551096,573002,649953,68131,695274,695305,711250,713983,719200,724869,743621,751815,76104,809993,946844,986623]],["@metamask/eth-qr-keyring>hdkey",[507520,821827]],["@metamask/eth-qr-keyring>uuid",[329214,427112,42756,433739,435635,579133,589243,611514,646280,852884,894057,995985]],["@metamask/eth-sig-util",[162924,371046,47994,57209,614147,621236,694157,852576,876521,884718,889949,937867]],["@metamask/eth-sig-util>@ethereumjs/rlp",[543820,799901]],["@metamask/eth-sig-util>@ethereumjs/util",[102198,193298,198564,209472,212876,224572,227526,230947,260237,297342,361511,3683,374639,390601,415846,495838,525453,627626,669475,670186,679441,729945,743747,7824,789337,789352,853979,875209,952208,971309]],["@metamask/eth-sig-util>@scure/base",[302420,96959]],["@metamask/eth-sig-util>ethereum-cryptography",[131710,369916,457095,518254,519021,961865]],["@metamask/eth-sig-util>ethereum-cryptography>@noble/curves",[173752,206056,220803,247916,394542,416989,492549,498307,576783,591346,629229,755930,790586,849595]],["@metamask/eth-sig-util>ethereum-cryptography>@noble/hashes",[122679,173646,337099,403269,529574,5324,556322,570641,59242,755859,760501,780128,845139,88131,889070,926106]],["@metamask/eth-snap-keyring",[264624,428805,509330,538699,557200,616374,628634,686329,688285,769031,814566,902219,995880]],["@metamask/eth-snap-keyring>@metamask/keyring-internal-snap-client",[342395]],["@metamask/eth-snap-keyring>@metamask/keyring-snap-sdk",[517441]],["@metamask/eth-snap-keyring>uuid",[287168,32493,580730,748716]],["@metamask/eth-token-tracker",[255353,521476,767110]],["@metamask/eth-token-tracker>@metamask/eth-block-tracker",[46097,607723,614362,624895,696478]],["@metamask/eth-token-tracker>deep-equal",[747174]],["@metamask/eth-token-tracker>deep-equal>es-get-iterator",[89048]],["@metamask/eth-token-tracker>deep-equal>es-get-iterator>is-map",[107274]],["@metamask/eth-token-tracker>deep-equal>is-date-object",[952632]],["@metamask/eth-token-tracker>deep-equal>which-boxed-primitive",[114003]],["@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-bigint",[1771]],["@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-boolean-object",[841928]],["@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-number-object",[523543]],["@metamask/eth-token-tracker>deep-equal>which-collection",[539681]],["@metamask/eth-token-tracker>deep-equal>which-collection>is-weakmap",[46066]],["@metamask/eth-token-tracker>deep-equal>which-collection>is-weakset",[954136]],["@metamask/eth-trezor-keyring",[194445,264654,741836,751374,763152,870611]],["@metamask/eth-trezor-keyring>@trezor/connect-plugin-ethereum",[654736]],["@metamask/etherscan-link",[174599,26449,303495,314846,450656,466760,633713,64025,695223,712830,759868,894858,947264,971443]],["@metamask/gas-fee-controller",[160643,310020,431866,599413,65293,899051]],["@metamask/gator-permissions-controller",[110501,142192,156998,287660,314123,335505,38997,424392,429712,466266,505027,547895,651900,686681,713139,747652,763604,769132,872242,875670,884890,925520,936022]],["@metamask/gator-permissions-controller>@metamask/abi-utils",[132430,161685,193591,294318,37582,391364,442168,466390,488652,610268,681258,716418,73598,74844,764636,7757,786764,820573,845545,935085]],["@metamask/gator-permissions-controller>@metamask/abi-utils>@metamask/utils",[162248,279794,296082,336582,398830,402812,475288,532135,607205,608880,646692,652494,711832,715618,757331,761098,824035,916807,921323,932986,969018]],["@metamask/gator-permissions-snap",[757501]],["@metamask/geolocation-controller",[315609,542024,656154]],["@metamask/geolocation-controller>@metamask/controller-utils",[444439,664050]],["@metamask/hw-wallet-sdk",[273429,493765,649775,711044,722299,784717,832813,853955,925338,959623]],["@metamask/institutional-wallet-snap",[986376]],["@metamask/jazzicon",[256985,762823,983303]],["@metamask/jazzicon>color",[796458]],["@metamask/jazzicon>color>clone",[901347]],["@metamask/jazzicon>color>color-convert",[665773,698052,793961]],["@metamask/jazzicon>color>color-convert>color-name",[670366]],["@metamask/jazzicon>color>color-string",[362611]],["@metamask/jazzicon>mersenne-twister",[760322]],["@metamask/json-rpc-engine",[106420,129385,140667,140667,157637,19352,19352,19352,19352,19352,199481,199509,238502,243714,314307,350026,354466,354466,354466,354466,354466,372429,382403,391113,395037,402896,414686,422356,422356,438025,482742,482742,482742,482742,482742,498989,51364,53248,54212,548170,556620,556620,556620,556620,556620,574527,574527,574527,574527,574527,578748,601837,647553,647553,647553,647553,647553,692881,69388,698064,703174,742547,742547,742547,742547,742547,787307,813216,813216,813216,813216,813216,821030,847163,858594,858594,858594,858594,858594,870967,886027,894454,897312,897312,897312,897312,897312,905416,905416,905416,905416,905416,908297,96214,96214,96214,96214,96214,97002,97002,97002,97002,97002,993793]],["@metamask/json-rpc-engine>klona",[654181,699479,747362,810045]],["@metamask/json-rpc-middleware-stream",[407394,407394,577656,643984]],["@metamask/json-rpc-middleware-stream>readable-stream",[104760,104760,123210,156997,156997,235139,278031,278031,304983,306788,306788,329687,329687,424983,424983,558254,558254,63063,63063,682145,700528,710347,710347,724843,724843,752314,752314,813254,820213,820213,825326,825326,839868,847866,847866,859321,859321,867208,906781,915142,925777,942412,942755,960094,979496]],["@metamask/keyring-api",[139070,161271,161934,17121,179447,189687,201831,207513,242317,286141,311332,341483,348554,354630,373585,39610,402239,416067,431348,456416,467236,469546,477322,510751,530237,53221,546277,556744,573028,592653,595704,607893,612293,614973,618809,619756,622416,670158,674397,689297,711298,713873,727517,751817,756597,76572,792581,848319,853429,861320,867525,871089,878215,886319,896322,906646,914976,928525,957740,970519,979855,996882]],["@metamask/keyring-controller",[280501,308565,43319,511133,869959,893653]],["@metamask/keyring-controller>@metamask/eth-simple-keyring",[232031,466615,670726,688668]],["@metamask/keyring-controller>@metamask/eth-simple-keyring>ethereum-cryptography",[11305,400353,460532,544758]],["@metamask/keyring-controller>@metamask/eth-simple-keyring>ethereum-cryptography>@noble/hashes",[223880,310270,685957,741197,812262,828940,932770,95840]],["@metamask/keyring-controller>ethereumjs-wallet",[391504,512249,562210,610527,741697,894416]],["@metamask/keyring-controller>ethereumjs-wallet>ethereum-cryptography",[120412,143313,1869,199175,260262,267378,283155,29554,361274,431383,442534,51747,564783,585825,61648,620662,723983,748852,749005,823638,94970,987807]],["@metamask/keyring-controller>ethereumjs-wallet>ethereumjs-util",[169479,206354,213421,255583,290409,303999,356547,388918,393539,456873,461780,531412,606439,613084,681551,681987,701971,75560,826014,851954,858500,892253,945458,968770]],["@metamask/keyring-controller>ethereumjs-wallet>utf8",[32600,670655]],["@metamask/keyring-controller>ulid",[31299,498756,599794,896795]],["@metamask/keyring-internal-api",[976690]],["@metamask/keyring-sdk",[172550,210385,314527,334016,413567,523985,693228,714140,779182,932754]],["@metamask/keyring-sdk>ethereum-cryptography",[103525,142909,42337,824745]],["@metamask/keyring-sdk>ethereum-cryptography>@noble/hashes",[10928,411983,465454,720650,756415,785108,821114,845020]],["@metamask/keyring-sdk>uuid",[266243,280255,345719,409470,682642,697490,831052,905303]],["@metamask/keyring-snap-client",[576446,656228]],["@metamask/keyring-snap-client>uuid",[210603,292899,580723,616586,724414,81254,968219,973252]],["@metamask/keyring-utils",[156635,364524,510930,551277,554909,61683,707315,790539,90678,924572]],["@metamask/logging-controller",[312137,704480,864342]],["@metamask/logo",[663411,739929,844113]],["@metamask/logo>gl-mat4",[58879,717641,733652,740435,974021,979173]],["@metamask/logo>gl-vec3",[239384]],["@metamask/message-manager",[778884,822403,888514,892833]],["@metamask/message-manager>@metamask/controller-utils",[187024,733931,834756]],["@metamask/message-manager>jsonschema",[17116,195728,489291,618744,657789]],["@metamask/message-signing-snap",[41218]],["@metamask/messenger",[132468,324960,446337,446337,446337,446337,446337,547368,547368,547368,547368,547368,728930,92275]],["@metamask/metamask-eth-abis",[110546,285981,294601,409227,501128,571397,632915,785012,882628,986848]],["@metamask/multichain-account-service",[112872,122562,184157,259468,266869,280918,326291,448197,466573,534335,550478,614513,670304,720318,724898,813193,948806]],["@metamask/multichain-api-client",[220677,366196,412454,4712,56710,675768,676687,991999]],["@metamask/multichain-api-middleware",[201424,290262,360985,365988,44375,706021,781281,882710,964508]],["@metamask/multichain-api-middleware>@metamask/api-specs",[128623,314788,67384]],["@metamask/multichain-network-controller",[15549,238301,305556,365769,578631,583231,90101,951493]],["@metamask/multichain-transactions-controller",[842180]],["@metamask/name-controller",[140701,166701,193354,314403,419490,420226,514121,530451,562227,801175,803418]],["@metamask/name-controller>@metamask/controller-utils",[812830,820184]],["@metamask/network-controller",[143149,152289,24414,310464,339710,368268,418084,469233,479558,520565,552682,636061,762180,85702,871933,877882,918748,964084]],["@metamask/network-controller>@metamask/eth-block-tracker",[336767,341783,347118,601556]],["@metamask/network-controller>@metamask/eth-json-rpc-infura",[196288,391341,473067,54642,597837,611576,717129,744077,877372,975366]],["@metamask/network-controller>@metamask/eth-json-rpc-infura>@metamask/eth-json-rpc-provider",[139596,139596,139596,139596,139596,163433,163433,163433,163433,163433,291600,357480,357480,357480,357480,357480,36276,64567,666594,666594,666594,666594,666594,865022]],["@metamask/network-controller>@metamask/swappable-obj-proxy",[101126,17647,354249,480251,526066,665751,832336,871023]],["@metamask/network-enablement-controller",[103362,115630,317286,723871]],["@metamask/notification-services-controller",[101843,106145,192982,19676,197760,221890,291105,303728,308033,346373,349332,375746,390923,433170,495805,510708,543059,543884,565553,599565,604977,629492,64369,651806,713264,713351,749512,760231,767678,767898,787532,795086,914806,923231,984642,989029,995144]],["@metamask/notification-services-controller>@contentful/rich-text-html-renderer",[528475,777316]],["@metamask/notification-services-controller>bignumber.js",[666371,807275]],["@metamask/notification-services-controller>firebase",[512308,578075,656851]],["@metamask/notification-services-controller>firebase>@firebase/app",[470481]],["@metamask/notification-services-controller>firebase>@firebase/app>@firebase/component",[616041]],["@metamask/notification-services-controller>firebase>@firebase/app>@firebase/logger",[38518]],["@metamask/notification-services-controller>firebase>@firebase/app>idb",[346418,877272]],["@metamask/notification-services-controller>firebase>@firebase/installations",[687603]],["@metamask/notification-services-controller>firebase>@firebase/messaging",[265738,92734]],["@metamask/notification-services-controller>firebase>@firebase/util",[41392]],["@metamask/object-multiplex",[136940,136940,373445,373445,541726,541726,657887,657887,967744,967744,993027,993027]],["@metamask/object-multiplex>once",[688655,688655,842744,842744]],["@metamask/object-multiplex>once>wrappy",[368616,368616,885067,885067]],["@metamask/object-multiplex>readable-stream",[103508,103508,108694,108694,15394,15394,181531,181531,183588,183588,258565,258565,284911,284911,292787,292787,304208,304208,319353,319353,446267,446267,472387,472387,478633,478633,540031,540031,554907,554907,593545,593545,659909,659909,66066,66066,666688,666688,691259,691259,729063,729063,737465,737465,75284,75284,835990,835990,838926,838926,839488,839488,846686,846686,884578,884578,934344,934344,979662,979662]],["@metamask/obs-store",[122300,214299,232983,283244,854077,983819]],["@metamask/obs-store>readable-stream",[27195,40045,445831,496410,517819,529089,561854,621489,739558,779210,802572,844312,874307,923699,945999]],["@metamask/passkey-controller",[138773,218032,253699,270306,376804,466756,474063,485540,504249,567228,665784,691697,697881,749002,772780,798478,971807]],["@metamask/passkey-controller>@levischuck/tiny-cbor",[220019,493552,782634]],["@metamask/permission-controller",[241361,241361,280346,282953,29947,29947,324825,408613,441099,441099,462105,462105,479312,523419,766840,775377,831851,914085]],["@metamask/permission-log-controller",[259599,975030]],["@metamask/permissions-kernel-snap",[957987]],["@metamask/perps-controller",[109005,131776,146767,146835,147715,166861,16793,172336,174548,175037,196734,245918,272322,305148,346778,364166,373663,375098,386261,3893,395119,491588,526637,531124,545599,550375,550715,584052,585609,58920,594397,643012,672347,679054,689897,731783,741649,748123,789705,798777,810634,814201,826868,829841,852270,861371,880754,887722,913593,94234,972819,981240,990288,99578,999037]],["@metamask/perps-controller>@metamask/abi-utils",[116976,219571,272986,331284,334918,384121,386804,453061,473419,496754,600352,706940,730423,754006,754647,755786,866792,868788,894907,985566]],["@metamask/perps-controller>@metamask/abi-utils>@metamask/utils",[185556,260050,293448,315141,408080,453552,481610,565621,577182,583069,584870,598924,601482,630273,667016,721999,765685,79050,813124,907068,980656]],["@metamask/perps-controller>@nktkas/hyperliquid",[104310,109780,117695,126567,129948,13122,132690,134558,136260,148576,150470,152238,152777,155866,160051,160212,172122,172348,179640,183434,18560,197246,202414,206361,209458,232607,238252,241692,255330,259296,262760,268552,270625,271713,275152,275874,276499,320642,326519,327618,327938,337336,341190,342125,343698,344020,368592,383673,385194,387209,392167,394517,395241,412173,417884,423124,425034,429317,429670,43298,434482,437988,440042,447958,451435,453765,469299,478198,478362,478572,489879,496559,49749,497865,501794,51875,527994,533203,541472,549794,55766,557761,562132,562644,565131,570471,583071,58517,592829,597190,604365,611035,614844,621657,628785,629027,640785,64224,65043,658208,658842,659457,666918,675165,682241,683450,684830,692635,70157,703655,706675,711065,711139,715410,719646,723835,726860,73209,734273,735072,738241,740695,741333,747952,748273,749123,760659,762251,766095,768199,769328,773136,77635,782054,783164,789670,792057,793757,79597,798285,798836,810924,812171,820195,827366,828565,829250,832381,832482,841020,841060,84664,852059,855435,872495,874382,875493,875859,88335,89070,893166,896315,899800,902314,910337,918025,924503,926684,937165,938067,93865,942032,949468,950833,951449,954322,962124,973117,977346,977395,988742,998918]],["@metamask/perps-controller>@nktkas/hyperliquid>@nktkas/rews",[745286]],["@metamask/perps-controller>@nktkas/hyperliquid>@noble/hashes",[104737,59573,720738]],["@metamask/perps-controller>@nktkas/hyperliquid>valibot",[907828]],["@metamask/phishing-controller",[179655,311290,379764,477648,661700,841681,910698,94168]],["@metamask/phishing-controller>@metamask/transaction-controller",[794611]],["@metamask/phishing-controller>ethereum-cryptography",[13676,461490]],["@metamask/phishing-controller>ethereum-cryptography>@noble/hashes",[151383,260127,323927,530685]],["@metamask/polling-controller",[217732,481268,716003,729986,816571]],["@metamask/post-message-stream",[101274,101274,107927,107927,23400,23400,359799,359799,379148,379148,411515,411515,465868,465868,524382,524382,543433,543433,620498,620498,74883,74883,755593,755593,822105,822105,927785,927785]],["@metamask/post-message-stream>readable-stream",[122587,122587,128093,128093,149890,149890,158647,158647,164196,164196,280932,280932,335992,335992,365149,365149,377228,377228,387923,387923,430723,430723,437116,437116,450432,450432,456224,456224,490137,490137,506348,506348,508142,508142,525366,525366,538997,538997,621123,621123,67395,67395,68193,68193,702682,702682,742819,742819,846471,846471,85990,85990,864992,864992,883886,883886,938361,938361,976199,976199]],["@metamask/ppom-validator",[317324,439250,44440,774755]],["@metamask/ppom-validator>@metamask/controller-utils",[156152,261765,44208,473335,650229,7688,990812]],["@metamask/ppom-validator>await-semaphore",[792539]],["@metamask/ppom-validator>crypto-js",[117376,135462,13944,166601,170649,180019,1972,256885,284030,303801,380204,385713,471792,51071,531696,533942,584919,597575,602073,619280,67012,718952,741309,806074,824624,826321,840925,86557,874575,897196,899533,926728,941380,944041,950736,953041,981178,983058,983925]],["@metamask/ppom-validator>json-rpc-random-id",[458834,84187]],["@metamask/profile-metrics-controller",[279742,381722,449601,759303]],["@metamask/profile-sync-controller",[125644,146021,183531,192614,266123,326838,340094,370622,392077,399923,408685,432448,473528,497660,54190,562397,574168,628147,699912,703447,726774,731171,743929,773579,785066,798631,863513,87602,893813,931824,953791,958387,978355,992137]],["@metamask/profile-sync-controller>siwe",[179635,218340,314810,6888,733878]],["@metamask/profile-sync-controller>siwe>@spruceid/siwe-parser",[151927,193476,814630]],["@metamask/profile-sync-controller>siwe>@stablelib/random",[291974,497547,536751,859089]],["@metamask/profile-sync-controller>siwe>@stablelib/random>@stablelib/binary",[465903]],["@metamask/profile-sync-controller>siwe>@stablelib/random>@stablelib/binary>@stablelib/int",[283731]],["@metamask/profile-sync-controller>siwe>@stablelib/random>@stablelib/wipe",[896039]],["@metamask/providers",[116263,152704,178618,482392,604632,611766,683527,725087,733762,748698,78279,798563,944401,946170,946822,958440]],["@metamask/providers>is-stream",[84773,902544]],["@metamask/providers>readable-stream",[125282,131581,167911,206930,217247,272419,275885,31329,31356,352992,360996,366175,373035,406951,433634,478694,577916,609843,616714,655772,660418,670086,719599,769499,777480,789321,817741,834278,871965,919766]],["@metamask/rate-limit-controller",[960504]],["@metamask/react-data-query",[574018]],["@metamask/react-data-query>@metamask/base-data-service",[718282]],["@metamask/remote-feature-flag-controller",[347168,647409,771708,773330,949849,969624]],["@metamask/rpc-errors",[132002,132002,132002,135299,135299,135299,135299,135299,144008,144008,16905,16905,195057,195057,195057,195057,195057,207534,207534,207534,207534,207534,220075,283232,353959,353959,353959,491065,581327,581327,584553,584553,584553,703640,703640,703640,703640,703640,711210,711210,711210,764010,805248,805248,875088,875088,875088,875088,875088,945500]],["@metamask/rpc-errors>fast-safe-stringify",[101292,101292,101292,754255,754255]],["@metamask/safe-event-emitter",[177805,323341,532596,664053,664053]],["@metamask/scure-bip39",[592190,595876,81675,951037]],["@metamask/scure-bip39>@noble/hashes",[153848,239227,282772,284016,40134,401576,493384,494981,602281,614013,826338,827658,835673,879240,88469,932221,938735,980895]],["@metamask/scure-bip39>@scure/base",[763261,817596]],["@metamask/seedless-onboarding-controller",[44298,489740,568481,58316,597094,673982,676672,987160]],["@metamask/seedless-onboarding-controller>@metamask/auth-network-utils",[499592]],["@metamask/seedless-onboarding-controller>@metamask/auth-network-utils>@toruslabs/constants",[633972]],["@metamask/seedless-onboarding-controller>@metamask/toprf-secure-backup",[139746,249917,296670,344341,486454,503758,555861,592245,59707,655886,693492,805151,874103]],["@metamask/seedless-onboarding-controller>@metamask/toprf-secure-backup>@metamask/auth-network-utils",[192016,218420,264439,448843,485152,617821,642486,995070]],["@metamask/seedless-onboarding-controller>@metamask/toprf-secure-backup>@toruslabs/fetch-node-details",[547778]],["@metamask/seedless-onboarding-controller>@metamask/toprf-secure-backup>@toruslabs/fetch-node-details>@toruslabs/fnd-base",[186037,29546,340414,389327]],["@metamask/seedless-onboarding-controller>@metamask/toprf-secure-backup>@toruslabs/fetch-node-details>@toruslabs/http-helpers",[33204]],["@metamask/seedless-onboarding-controller>@metamask/toprf-secure-backup>@toruslabs/http-helpers",[875592]],["@metamask/selected-network-controller",[500662,722670]],["@metamask/shield-controller",[264749,298080,392003,395525,645148]],["@metamask/shield-controller>@metamask/controller-utils",[669506,755073]],["@metamask/shield-controller>@metamask/transaction-controller",[229162]],["@metamask/signature-controller",[147818,353121,415436,521464,535278,585130,602709,80579]],["@metamask/smart-transactions-controller",[194050,273538,30449,342310,407608,492777,500412,541149,612157,631561,847512,878349,95789]],["@metamask/smart-transactions-controller>bignumber.js",[22178]],["@metamask/snap-account-service",[296184,600884,705758,720229]],["@metamask/snaps-controllers",[148130,211576,297171,313696,346729,367752,409994,444711,461950,556807,561294,577326,579802,597831,630702,67054,675694,711526,730480,741600,75248,757707,794568,892007,944997,979892]],["@metamask/snaps-controllers>@xstate/fsm",[266383]],["@metamask/snaps-controllers>concat-stream",[620330]],["@metamask/snaps-controllers>get-npm-tarball-url",[352717]],["@metamask/snaps-controllers>readable-stream",[123226,204183,254274,326552,516256,531867,601617,613720,66178,773003,794997,838196,904542,917006,961593]],["@metamask/snaps-controllers>readable-web-to-node-stream",[185911]],["@metamask/snaps-controllers>readable-web-to-node-stream>readable-stream",[142272,157503,176810,222566,302450,343052,433448,472649,513564,578847,619877,771129,878666,959995,99080]],["@metamask/snaps-controllers>tar-stream",[102375,562629,575068,710146,79433]],["@metamask/snaps-controllers>tar-stream>b4a",[263164,521570,537710,561576,627539,955346]],["@metamask/snaps-controllers>tar-stream>fast-fifo",[121649,771765]],["@metamask/snaps-controllers>tar-stream>streamx",[976112]],["@metamask/snaps-controllers>tar-stream>streamx>queue-tick",[24228]],["@metamask/snaps-execution-environments",[449787,449787,897911]],["@metamask/snaps-registry",[416543,517254]],["@metamask/snaps-rpc-methods",[112406,113452,116336,129293,130982,134718,14158,164539,16908,181432,18435,210734,212396,218959,230448,247141,253170,253662,288852,294311,301028,305776,315290,355340,372996,377753,402414,412158,434878,434878,459849,46547,467304,472860,473144,477945,521406,53049,538650,590622,593680,600068,607421,60968,62458,645495,655121,660073,689132,689132,709716,760734,763859,776458,796466,802191,815131,825459,832436,840672,846787,850379,850493,871069,89132,899342,899403,910256,911111,927714,969866,981945,982071,992416,999482]],["@metamask/snaps-sdk",[102782,115412,157392,157392,159167,159167,163980,174638,174638,186119,186119,188320,188320,208554,208554,216155,254995,254995,274422,285081,29765,300005,300005,32014,32014,33029,33029,335562,335562,344706,37511,382906,382906,392154,396124,414221,414221,429922,434322,434322,443697,443697,45217,45217,453945,453945,461893,461893,484068,484068,495699,499490,499490,514309,515828,515828,544299,544299,555968,559152,5654,5654,57202,597361,597361,609948,609948,614130,614130,633089,633089,647388,647388,64798,657612,676358,676358,681294,689686,689686,694729,694729,699048,706524,706524,721117,721117,722837,722837,728195,728195,773466,78121,78121,78974,797999,797999,80332,80332,814006,814006,818365,818365,825129,833399,833399,833414,833414,842294,861913,861913,869864,869864,878884,879516,879516,879771,879771,884824,896514,902760,936435,936435,937053,937053,955187,955187,971188,971188,98414,984524,984524,988068,988068]],["@metamask/snaps-sdk>@metamask/key-tree",[100468,111999,141769,217774,224378,256046,268988,302322,35275,376978,379669,385992,401771,410574,42741,429080,433368,460538,476536,480665,500846,508238,515430,53921,568607,611155,611777,64263,650475,677015,682109,693932,697917,732112,734086,854828,872266,88321,920131,94947,949840,963624]],["@metamask/snaps-utils",[106292,116243,125517,140657,156828,190258,191510,214250,237825,246146,252164,253358,274065,290282,298523,305082,353963,355897,358e3,385966,392380,430595,431050,439215,467320,480218,504536,54872,556550,619193,62099,630249,631524,642135,64902,649571,650976,666849,668987,67069,676798,685502,712,722312,749974,752260,761368,776622,790516,83472,843881,871120,88074,90157,903038,90404,912022,914420,919190,939241,958657,968074,96974,987002,988931,988950,98911]],["@metamask/snaps-utils>@metamask/slip44",[847408,976920]],["@metamask/snaps-utils>fast-xml-parser",[212862,311719,314871,418097,499075,56201,574526,635939,701721]],["@metamask/snaps-utils>fast-xml-parser>@nodable/entities",[282373,975253]],["@metamask/snaps-utils>fast-xml-parser>path-expression-matcher",[239362,294568,473330]],["@metamask/snaps-utils>fast-xml-parser>strnum",[381586]],["@metamask/snaps-utils>marked",[355251,44747]],["@metamask/snaps-utils>rfdc",[397348,965459]],["@metamask/snaps-utils>validate-npm-package-name",[226237,266332]],["@metamask/snaps-utils>validate-npm-package-name>builtins",[283844,81481]],["@metamask/solana-wallet-snap",[217919]],["@metamask/solana-wallet-standard",[158133,29645,309289,819292,876553]],["@metamask/solana-wallet-standard>@solana/wallet-standard-features",[45444,527170,598497,943760]],["@metamask/solana-wallet-standard>@wallet-standard/features",[694718,716207,986059]],["@metamask/solana-wallet-standard>@wallet-standard/wallet",[295412,302163]],["@metamask/storage-service",[108300,284695,338363]],["@metamask/subscription-controller",[135109,234144,31201,371900,663425,687301,861421,942463]],["@metamask/subscription-controller>bignumber.js",[6934]],["@metamask/superstruct",[142827,142827,147698,147698,147698,147698,147698,147698,147698,159784,174074,179379,179379,179379,179379,179379,179379,179379,244231,244231,269960,290266,290266,290266,295771,315560,315560,315560,315560,315560,315560,315560,342672,342672,355608,355608,356583,356583,411554,411554,411554,448967,448967,448967,449070,449070,460719,497177,497177,497177,497177,497177,497177,497177,5136,5136,5136,5136,5136,5136,5136,545203,545203,545203,572857,599805,599805,599805,599805,599805,599805,599805,605470,612815,612815,612815,628674,628674,628674,628674,628674,628674,628674,638737,638737,638737,638737,638737,638737,638737,652825,652825,652825,784225,784225,878379,982944,982944,982944]],["@metamask/test-dapp-solana>@solana/wallet-standard-chains",[826167]],["@metamask/transaction-controller",[113784,129438,133660,145895,15420,158388,16762,174838,196832,200881,204471,212734,247702,24889,283806,284742,294998,317525,333136,334940,348372,354166,366703,401604,420762,443975,446675,450915,451275,454515,459550,473678,482355,486568,491993,493646,523615,53002,539542,546292,57529,579150,581224,590020,592361,598279,600795,600993,601673,607402,619783,622702,623476,637434,660227,660502,684871,685128,699924,71530,730691,731521,735330,736572,755199,757560,769434,774464,777496,780690,788457,795104,795886,80667,850156,857157,883847,885377,8862,897424,900682,907315,907628,910368,910917,940636,941717,963648,97519,976022,978561,992657]],["@metamask/transaction-controller>@metamask/nonce-tracker",[111187,753684,775896,877795]],["@metamask/transaction-controller>@metamask/nonce-tracker>async-mutex",[160583,224172,420968,517950,538693,596941,616599,751816,793012,857279,955353,997852]],["@metamask/transaction-controller>bignumber.js",[70861,717341]],["@metamask/transaction-pay-controller",[114558,130406,132650,212921,225985,252102,265252,279765,286559,293522,3374,363506,367401,369931,376762,382126,387286,40909,438537,440906,460820,481511,482232,490270,515223,536724,537241,567137,571657,586022,620880,628972,641985,654705,658276,670562,672603,685993,70208,702673,707468,710291,714298,719107,729938,782936,789235,807109,852806,860773,899465,911876,926586,926676,932378,948928,955395,968903,971863,976393,978337,981657,989e3,990999]],["@metamask/transaction-pay-controller>@metamask/ramps-controller",[300900,696700]],["@metamask/transaction-pay-controller>bignumber.js",[708476]],["@metamask/tron-wallet-snap",[266372]],["@metamask/user-operation-controller",[160354,249322,272010,355601,379274,390665,484013,667827,792355,798564,826455,941891]],["@metamask/utils",[103453,103453,103453,103453,103453,103453,103453,108401,114328,142282,142282,145202,161277,166378,166378,166378,166378,166378,166378,166378,173921,182498,201839,204179,204179,204179,204179,204179,204179,204179,211600,230855,230855,230855,230855,230855,230855,230855,231267,258862,258862,269530,269530,269530,269530,269530,269530,269530,297564,297564,301885,301885,301885,301885,301885,301885,301885,303557,319939,334031,334031,334031,334031,334031,334031,334031,364705,364705,364705,364705,364705,364705,364705,379054,379054,379054,379054,379054,379054,379054,38333,38333,38333,38333,38333,38333,38333,418021,418021,418021,418021,418021,418021,418021,418181,432315,432315,432315,432315,432315,432315,432315,433151,447519,447519,447519,456038,47631,481009,481009,481009,481009,481009,481009,481009,489064,502257,502257,502257,502257,502257,502257,502257,507060,507060,507060,507060,507060,507060,507060,513458,51464,536560,536560,536560,536560,536560,536560,536560,549140,554839,554839,554839,558490,570302,570302,570302,570302,570302,570302,570302,572433,572433,572433,572433,572433,572433,572433,609419,624460,691991,691991,691991,691991,691991,691991,691991,698087,699844,699844,699844,699844,699844,699844,699844,705025,705025,745085,745085,745928,755244,755244,755244,755244,755244,755244,755244,760184,760184,761788,776272,787916,791443,798190,812046,812805,812805,812805,815212,818337,818337,823663,832018,832995,845970,851754,870601,870601,870601,870601,870601,870601,870601,876025,889333,889333,889333,889333,889333,889333,889333,894651,896639,896639,908743,908743,933647,933647,933647,933647,933647,933647,933647,934538,935406,939256,971968,973594,973594]],["@metamask/utils>pony-cause",[178430,181686,207912,341875,357464,400317,642069,67282,762565,826117]],["@metamask/wallet",[185318,230222,258566,261508,278314,33594,547752,598086,73520,742902,923405]],["@mui/material",[104312,11577,11847,127519,131770,133546,133610,134295,138369,149615,153167,156273,157655,162330,165360,166451,167754,167889,178627,181078,181235,189302,191831,203048,210303,226316,236307,255651,259731,26139,2653,282411,301846,307879,310781,313877,324435,332447,332703,336669,341331,35299,35395,365663,368447,370166,378470,379241,38422,398360,412251,413825,416935,425277,431563,436002,440400,450283,452141,454296,465673,471225,473091,479487,501597,514651,519621,531344,538827,548057,551018,55753,569241,57703,578155,57903,590551,591867,597805,599115,6059,609711,61123,614039,624277,62485,632116,640422,641503,648848,654282,656872,661831,663415,66571,671692,676437,678803,682879,685075,689227,700221,714326,715498,767335,768420,812063,818175,819181,822498,834867,836235,852735,860482,867615,879514,886401,895557,901045,90255,909476,91357,917195,920763,925855,928405,933304,94413,945520,945831,955653,963413,965979,97417,989167,989507,991447,999946]],["@mui/system",[112307,157747,170487,223596,260499,292499,337791,382928,508125,51009,518028,521462,559495,571389,573633,613431,627531,740860,75139,752367,759456,767479,768766,773517,800001,801105,828135,87567,884047,901626,927296,961052,967443,97900]],["@mui/system>@mui/private-theming",[57094,573456,603025,82634]],["@mui/system>@mui/styled-engine",[184884,472395,669950]],["@mui/system>@mui/utils",[103354,184229,1975,20613,214359,230793,246517,282805,291577,305397,319,331467,331569,394779,418965,439189,448157,486545,487849,498525,503031,510163,540913,554911,557889,599139,632271,650543,711433,727645,768304,781887,79181,843102,850845,856709,875719,902965,958525,991061,996063]],["@mui/system>@mui/utils>react-is",[254918]],["@mui/x-date-pickers",[10168,10283,109947,111395,122804,123803,126836,129352,135,137138,143620,14500,193795,207533,217914,232699,236e3,240425,252109,253626,256113,276833,28014,282147,286591,291798,296702,297337,299813,306965,312931,31307,31610,324552,346464,347478,360213,367588,371017,373436,407675,409265,427557,428868,43945,439705,449361,450172,456280,462684,465385,471109,472329,475479,481776,493444,495730,509819,516586,531919,534334,535112,549645,559442,560807,57035,575472,575759,576361,591276,613923,621225,62313,636789,637605,644658,645967,664886,684598,696035,696877,722351,731545,735574,743304,748043,76734,777039,79095,794182,794335,797343,802198,802583,804689,807381,81821,836036,837819,842867,844151,847094,860107,861581,864041,868232,872762,881645,883161,888956,903160,904440,909821,916237,918664,922167,922940,923449,92574,931514,939733,946300,948710,983447,984247,995814]],["@mui/x-date-pickers>@mui/utils",[119651,197021,248723,261091,302419,340611,352023,365965,48343,529819,586991,63207,646853,676243,677617,73013,77457,789905,803499,86397]],["@ngraveio/bc-ur",[10198,210805,216814,226530,314138,334683,347103,396333,526436,585651,608778,669916,715987,750651,757357,767373,776950,816060,84968,862909,893188,903681,912490,916561]],["@ngraveio/bc-ur>@keystonehq/alias-sampling",[836484,868785]],["@ngraveio/bc-ur>assert",[100734,151184,158196,215851,63741,784333,788609,883762]],["@ngraveio/bc-ur>assert>is-nan",[247643,277973,453632,461010,742216,787145,924544,935775]],["@ngraveio/bc-ur>assert>object-is",[129730,180974,288097,331205,628587,669991,827856,864250]],["@ngraveio/bc-ur>bignumber.js",[574149,853482]],["@ngraveio/bc-ur>cbor-sync",[14269,632362]],["@ngraveio/bc-ur>crc",[136322,152617,219649,230219,232305,244414,274359,299098,389601,40594,416638,457640,463838,524395,524523,61918,633555,739574,761450,76563,796502,807767,852556,858449,878551,888882,902251,946884]],["@ngraveio/bc-ur>crc>buffer",[359088,797843]],["@ngraveio/bc-ur>jsbi",[623474,847743]],["@ngraveio/bc-ur>sha.js",[132806,158146,240184,268651,312053,363368,381195,505109,576585,588986,637803,699859,741756,774747,797502,971836]],["@ngraveio/bc-ur>sha.js>to-buffer",[715425,971502]],["@noble/ciphers",[103250,193952,215500,305394,539353]],["@noble/curves",[215644,245215,312851,341076,362271,36773,391582,422644,446266,489928,522803,557246,58340,589072,610537,620493,657726,673049,761030,792499,805134,838156,90800,909314,927500,982322,992425]],["@noble/hashes",[117154,128961,15426,163684,202356,237402,27084,279307,288537,347774,361367,362108,367013,38578,399502,41903,451786,459925,477964,477964,494212,496153,501585,505886,57158,641239,645584,65716,661330,661330,671955,671955,691176,716070,716070,720343,770999,772169,780441,798518,850479,85428,864832,943940,943940,975651,975651,992212]],["@open-rpc/meta-schema",[429094]],["@open-rpc/schema-utils-js",[312700,426923,835483]],["@open-rpc/schema-utils-js>@json-schema-tools/dereferencer",[106132,574712]],["@open-rpc/schema-utils-js>@json-schema-tools/dereferencer>@json-schema-tools/traverse",[442980]],["@open-rpc/schema-utils-js>@json-schema-tools/meta-schema",[912036]],["@open-rpc/schema-utils-js>@json-schema-tools/reference-resolver",[24892,482871,648208,859621,916668]],["@open-rpc/schema-utils-js>@json-schema-tools/reference-resolver>@json-schema-spec/json-pointer",[684339]],["@open-rpc/schema-utils-js>is-url",[409836]],["@open-rpc/test-coverage>isomorphic-fetch",[605701]],["@open-rpc/test-coverage>isomorphic-fetch>whatwg-fetch",[768451]],["@popperjs/core",[104262,120185,131500,134115,149922,172285,183817,201918,206556,218858,226744,25019,262272,289140,302530,326635,330629,335526,33565,351475,3598,400267,492560,50696,513223,532874,553918,568598,589833,638543,659638,674110,680243,70361,750319,757155,762019,773577,790791,794063,814127,815258,818832,826916,843022,864542,872787,886298,891016,908905,925448,947862,954239,978752]],["@reduxjs/toolkit",[363117,55820]],["@reduxjs/toolkit>reselect",[280614,317341,800725,93958]],["@rive-app/react-canvas",[913965]],["@rive-app/react-canvas>@rive-app/canvas",[236494,236494,236494,236494,236494,888132]],["@scure/base",[167794,401064,54584,591315]],["@segment/analytics-node",[135879,143928,163263,23300,271148,279322,32883,335978,340597,340730,34948,365146,385801,462823,499454,521632,525457,529724,617928,65280,653229,654187,668435,677885,679751,703484,71633,726152,737101,744764,778153,808463,816565,881020,885160,905068,926980,94823,950625,955779,968015,991406]],["@segment/analytics-node>@lukeed/uuid",[198902,43220]],["@segment/analytics-node>@segment/analytics-core",[102288,12916,160021,160977,171519,175194,184523,194733,20572,210822,243329,265654,282999,395707,416644,417256,420293,433490,443705,489300,549335,558012,564798,58131,599055,681279,706813,70932,781258,847051,847214,858693,863234,889906,946716,956877]],["@segment/analytics-node>@segment/analytics-core>dset",[354970,433864]],["@segment/analytics-node>@segment/analytics-generic-utils",[267284,556176,927339,958351]],["@segment/analytics-node>jose",[115208,116941,134823,171121,178168,218007,222891,23030,244431,248337,260779,322590,352649,371843,373544,378729,395627,430659,435518,463860,470658,501763,527336,53295,566761,569824,577658,589323,615640,663478,67737,678296,723893,732642,740178,755924,796358,8143,850867,851454,877028,877324,892346,896511,898354,909979,925336,936995,953385,968646,98100,989618]],["@sentry/browser",[106438,106438,130760,130760,14635,155001,162183,185635,195829,216295,216295,224245,224245,244880,266615,266615,273521,273521,279802,327566,327566,360023,360023,366523,369735,369735,382128,392788,392788,43417,443227,443227,455142,466024,472847,47810,47810,494688,494688,503510,503510,535279,537252,537252,538564,550041,550041,553205,553205,564350,571893,591386,591386,606189,639781,642735,642735,659129,659129,707995,707995,717309,717309,723808,747402,747402,748028,753036,763935,795966,810087,845226,845226,851781,851781,868888,868888,892145,902419,902419,943544,943544,96434,982238]],["@sentry/browser>@sentry-internal/browser-utils",[104168,104168,117529,117529,12796,12796,132076,132076,133481,133481,138716,184748,184748,185335,185335,185746,185746,19467,225669,225669,234512,234598,234598,259463,259463,303818,303818,314408,327140,327140,33040,406097,406097,417860,417860,441265,459517,459517,495242,495242,51450,515400,533858,533858,566632,56680,57324,621827,662925,676979,681747,681747,702053,71337,714599,714599,74342,756025,756025,764651,764651,765698,768571,772879,814601,821396,858586,858586,863531,863531,879954,882555,882555,898026,898026,903217,932294,932294,956354,956742,956742,975431,978802,993671]],["@sentry/browser>@sentry-internal/feedback",[178066,666012,666012]],["@sentry/browser>@sentry-internal/replay",[117172,117172,949306]],["@sentry/browser>@sentry-internal/replay-canvas",[928535,928535,986415]],["@sentry/browser>@sentry/core",[105388,105388,115433,115433,122411,123532,125617,125617,136244,136244,137891,137891,138706,138706,140722,140722,145834,145834,153839,153839,155682,155682,15797,16278,16278,16686,16686,17072,172900,173177,173177,175384,178061,179184,179184,187474,187763,187763,187973,189193,191895,191895,192279,192279,198066,198066,201740,24708,24708,254759,254759,267276,267276,276277,276277,276435,285803,290264,290264,295088,298556,329537,341035,352158,355989,367877,367877,369793,398471,39859,405971,405971,410710,411335,420376,438774,438774,441227,441227,444284,461582,466737,468417,48718,48718,488560,513234,5152,52018,532725,532725,534098,534098,538979,542764,548697,550866,577102,584222,584222,587044,587044,597014,597014,59824,598723,608119,608119,612717,631905,631905,664746,665016,671480,67904,67904,682631,691963,691963,704776,707212,709356,713966,71409,71409,718800,718800,719149,719149,719509,719509,724666,724666,730074,730074,76838,76838,768881,768881,77614,77614,777217,777217,778313,778552,78463,793111,793111,803537,803537,808106,808106,812863,812863,818747,818747,827284,836164,836164,837971,837971,848294,865961,884405,884405,884488,884488,901814,901814,902309,903226,903226,911216,920938,92376,92376,931263,933190,933190,934379,939543,943924,960196,960196,960767,96331,96331,967173,973149,973149,973234,973234,98154,986746,986746]],["@sentry/utils",[107842,107842,1090,109910,148366,151201,16786,16786,179329,179329,182881,230337,230337,25605,25605,283049,316310,370861,37853,37853,384255,384255,38561,388006,388006,397718,397718,401967,40209,40209,402228,414753,424264,424264,425535,425535,450579,450579,462128,471265,471265,490521,494945,494945,497577,513064,520348,536275,538600,538600,562298,562298,566612,571825,571825,572858,572858,586312,586312,605257,613608,620209,620209,6246,644094,644094,646493,648017,648017,650773,654761,654761,665812,669891,680985,680985,696294,696294,708521,709502,716547,74263,766221,766221,769233,785755,799130,799130,814508,821016,821016,830339,830339,833097,834028,834028,834529,834529,837075,837075,84607,851338,851338,85182,85182,856928,879561,895315,895315,906769,906769,921368,940344,940344,950825,973544,97407,97407,988217,988217]],["@simplewebauthn/browser",[130116,134797,173983,216354,311050,322193,328784,345592,35049,430850,454807,482346,50783,534444,537185,600306,693695,750119,80287,833807,891367,931567,934135,955988,998633]],["@solana/addresses",[500089,87145]],["@solana/addresses>@solana/codecs-core",[531837,839037]],["@solana/addresses>@solana/codecs-strings",[694842,726472]],["@solana/addresses>@solana/errors",[410059,652139]],["@storybook/addon-docs>remark-external-links>mdast-util-definitions",[603936]],["@storybook/react>util-deprecate",[381763,381763,79894,79894]],["@tanstack/react-query",[224732,237278,493565,511705,599973,630844,842109,866471,940025,967358]],["@tanstack/react-query>@tanstack/query-core",[100980,119828,140390,151235,177221,248801,286636,330821,367269,377322,38312,438488,453663,530095,536570,569974,586235,612194,635470,645876,656599,665,753269,78174,816750,820513,82268,858515,898427,901399,92190,995833]],["@tanstack/react-query>use-sync-external-store",[11853,941760]],["@tanstack/react-virtual",[207896]],["@tanstack/react-virtual>@tanstack/virtual-core",[282889,737520]],["@toruslabs/eccrypto",[510991]],["@toruslabs/eccrypto>elliptic",[206133,220827,24812,26161,266482,306768,31289,350877,385483,393187,431844,439410,445919,504347,505841,520526,543260,560923,56160,595344,598866,601480,648722,671066,673096,723810,756924,834229,857725,917768,917768,917768,917768,917768,917768,917768,97907,995991]],["@toruslabs/eccrypto>elliptic>brorand",[700493,754298]],["@toruslabs/eccrypto>elliptic>hmac-drbg",[178403,939456]],["@toruslabs/eccrypto>elliptic>minimalistic-assert",[147749,993586]],["@toruslabs/eccrypto>elliptic>minimalistic-crypto-utils",[178175,276212]],["@trezor/connect-web",[115319,161947,264637,272084,334331,387724,448771,475227,511005,58278,676994,690222,72012,770573,777401,802974,839726,883249,895143,904484,932425,940370,942600,948414]],["@trezor/connect-web>@trezor/connect",[10025,108752,122517,12270,141773,150522,151165,161174,190159,195279,203181,216078,231494,266718,274388,277055,283080,314251,323965,327912,329191,342593,345251,3467,347648,360800,381398,390491,40275,40574,416188,43960,451946,458880,478494,489630,497326,507351,515009,517530,517669,531360,553483,565501,56800,574164,595757,608124,620541,620568,644936,646784,655131,659703,66501,686693,699779,701362,715952,725136,728359,735653,740096,740975,74383,75084,763550,764876,767847,771544,773642,792108,794554,799799,819892,823473,832029,841885,845438,860263,878923,896867,905327,92633,941442,945725,946769,949565,95052,965279,986858,989118,989991,996616,997540,999030]],["@trezor/connect-web>@trezor/connect-common",[32142,371709,381636,439606,494623,556102,745347,881967]],["@trezor/connect-web>@trezor/connect-common>@trezor/env-utils",[314353,410764,53958,759514,893317,973721]],["@trezor/connect-web>@trezor/connect-common>@trezor/env-utils>ua-parser-js",[690253,959498]],["@trezor/connect-web>@trezor/connect>@trezor/blockchain-link>@trezor/websocket-client",[34818,363330,464687,47679,487483,922962]],["@trezor/connect-web>@trezor/connect>@trezor/device-utils",[103192,292761,358991,389452,406597,586775,670190,716385,781842,817832,886318,892554,903089,913937]],["@trezor/connect-web>@trezor/connect>@trezor/protobuf",[192040,206351,224121,239021,311145,331427,523596,534276,669094,783184,822449,889390,969356,974893]],["@trezor/connect-web>@trezor/connect>@trezor/protobuf>long",[229996,32900]],["@trezor/connect-web>@trezor/connect>@trezor/schema-utils",[122668,261702,342180,359360,379509,463685,484613,508198,547183,585053,735599,736876,813617,898126,948506,984401]],["@trezor/connect-web>@trezor/connect>@trezor/schema-utils>@sinclair/typebox",[10071,100733,102130,103796,110900,111776,112236,117284,118003,118804,119200,123788,127040,130473,132911,136823,137584,147967,155699,156134,159565,160244,160650,160863,16791,168041,169820,170758,171039,172991,174218,175584,178057,181915,186315,187089,188342,191637,194706,195856,197250,200299,201099,201769,204592,206718,208399,208829,210369,214286,215793,216042,219050,220746,220944,229684,236703,238830,239055,239292,242637,245444,247839,249206,254583,257519,257695,259428,25964,259932,260556,265631,26584,266034,268431,271501,271739,274396,277379,283058,28818,293830,298565,301031,304363,31117,31199,312491,314851,318295,319196,319867,32976,329881,331519,331682,332271,335570,341314,343978,345602,34641,346487,349811,351009,354589,355440,362667,362796,364835,365852,367026,367215,373225,37588,379348,380795,381147,382219,383298,387371,390546,39217,393392,394828,398387,403763,404401,405919,406295,407776,407783,408437,408619,409462,409603,409653,410500,410871,412896,415827,415965,421427,422288,423120,424426,430514,430971,433803,436271,444812,447676,448635,449922,454835,463315,465701,466e3,466580,467378,467452,468373,468448,469696,471615,476897,47863,481167,482649,48745,489560,49638,498822,501984,503150,50320,504217,50501,505749,505954,50615,50686,507671,50892,51314,51590,517437,525073,526787,528259,529709,529967,538011,538649,540152,54028,547506,549043,549475,552736,557183,559614,560885,561224,561555,562097,56643,572055,573014,575449,57744,582371,583259,583492,587870,588569,590019,593512,593712,595154,59605,596773,59823,600804,606394,60711,607170,608015,609038,616756,617912,621097,621237,626993,627324,628264,630094,63092,632188,634166,635952,637094,638924,639144,646480,650258,652547,652606,653368,655535,657502,65932,66004,661966,664900,668354,670079,671534,672327,673921,678102,683755,684089,685526,687162,688581,689850,6909,691341,69587,695871,696340,702304,712099,713608,717272,719546,720281,722276,722688,724670,725168,72857,731968,732863,733547,738595,741595,747896,751934,753591,756897,757749,760170,760233,761770,763083,769314,771350,778113,778184,778881,780967,781247,783082,786415,788050,791141,791780,792063,793685,798959,799272,799516,804343,804806,805096,806053,808118,808800,810711,811224,81164,813696,813970,814483,8156,816546,817460,818560,825131,827098,830144,830570,834141,834870,836330,838363,842182,842900,843683,844162,845483,846752,848123,848148,848245,849448,850066,851479,853339,854335,854521,856410,856465,859079,859375,861799,86268,8659,86775,868260,8688,871056,874423,876464,877395,878559,880937,888891,889739,891552,893015,896175,897100,899128,901930,904973,905518,906404,912057,913407,916792,91810,922572,925046,928016,929194,932286,93690,937600,93946,951275,952005,955668,956704,957389,96495,96669,971233,971642,972457,972501,976667,979371,980367,980539,988942,99035,994890,995631,997471]],["@trezor/connect-web>@trezor/connect>@trezor/transport",[10733,203388]],["@trezor/connect-web>@trezor/utils",[105122,114422,118452,127677,140895,144958,149083,151988,152458,163960,167371,168562,184625,193114,196811,198189,232420,240990,245289,245471,257808,267207,267640,286889,297908,303251,309599,312634,312898,315922,317668,327897,3283,328877,337688,34512,345701,354450,360391,364734,376797,377702,386474,38717,391697,392260,396482,398672,400898,402625,442780,468313,470425,473116,484081,486057,488143,507929,514914,540608,54404,549067,551151,562303,563218,600807,610477,618189,624942,635766,639474,644889,656658,662552,668030,668094,671958,672322,673885,674656,680084,682727,686691,689593,700160,702946,706191,707446,707804,710215,711619,727253,744625,746311,753182,755685,763770,771622,773861,777833,805328,805501,810337,814213,818546,821066,834661,842779,85057,853904,871167,87568,887517,891001,897150,914171,961652,97101,977779,979738]],["@trezor/connect-web>@trezor/utils>bignumber.js",[521034,549083]],["@zxing/browser",[145953,147414,301448,342264,585117,594168,657902,717209,729074,754576,855256,877446]],["@zxing/library",[102076,104640,105846,10967,118907,130552,131671,135525,13619,137253,147843,148535,157062,161840,162502,165773,173036,177378,177605,181600,182358,1880,192328,200985,204042,211185,214711,217403,220502,222151,225176,226658,226843,231804,245348,245586,256598,265347,267647,281891,283130,283402,290294,290552,292589,30383,305577,30700,312627,313691,318681,322242,326170,330187,33047,331102,342062,344837,344937,348944,350023,350110,353827,35702,358354,36393,364077,366804,367456,37933,382336,38382,384185,389157,391484,395347,398079,398319,403738,410854,413135,414480,420387,426748,429613,447649,448751,448788,452848,454274,467294,470216,475173,476225,480383,48100,4886,490735,491694,495292,511410,512766,51355,517495,520474,524483,533622,543903,545034,550786,5641,567973,568293,576257,579657,58251,595812,599545,602724,604879,605398,606450,608296,618081,618221,628824,628900,633971,633978,636179,638450,639014,643367,643977,659159,66029,670237,674724,689980,690012,693466,696602,696739,701767,702808,70813,7139,715814,717651,720949,723205,726724,731223,731411,73343,734567,739843,744838,754217,762947,764246,770429,77429,781645,795293,805428,805970,809671,810595,812056,812169,826170,845566,84931,849943,853708,862070,863850,865388,873614,879385,881821,887588,887774,888951,895334,902900,907072,923877,935419,935949,939171,943402,946912,959134,96263,964206,966391,972327,978368,980892,981228,992729,993255,993733,99546,996484]],["@zxing/library>ts-custom-error",[325932]],["addons-linter>deepmerge",[239016,900583]],["async-mutex",[34965,350147,368386,558744,629233,788581,919969,945539]],["base32-encode",[91703]],["base32-encode>to-data-view",[351418]],["base64-js",[223159,223159,685590,685590]],["bignumber.js",[468257,60746]],["bitcoin-address-validation",[272909,879040]],["bitcoin-address-validation>bech32",[54716]],["bowser",[598640,598640,684003]],["browserify>concat-stream>typedarray",[935771]],["browserify>has>function-bind",[500185,68276,796300,819495]],["browserify>string_decoder",[242714,242714,938453,938453]],["browserify>url",[251820,558163]],["browserify>url>punycode",[646246,855041]],["browserify>util",[204191,276330,320722,333961,807928,826803]],["browserify>util>is-arguments",[635067,790588]],["browserify>util>is-generator-function",[664264,673321]],["browserify>util>is-typed-array",[242256,518327]],["browserify>util>which-typed-array",[601644,708759]],["browserify>util>which-typed-array>for-each",[227345,541290]],["bs58",[121295,121295]],["bs58>base-x",[908463,908463]],["buffer",[916794,916794,971567,971567]],["buffer>ieee754",[170059,170059,305992,305992]],["chalk",[280227,289568,620047,652378,912963,995050]],["chalk>ansi-styles",[780723,845064]],["chalk>ansi-styles>color-convert",[179422,286427,32004,547055,969867,997664]],["chalk>supports-color",[381047,469146]],["chart.js",[137490,464071]],["chart.js>@kurkle/color",[283251]],["clsx",[92288]],["cockatiel",[126685,177086,181214,182234,229411,286308,286985,324161,380736,496021,503798,50519,507271,514296,516526,519577,524656,550106,606424,686779,690468,733066,755020,780659,791579,811100,822175,826585,84889,893114,90053,902516,911475,926489,939590,940367,945180,945924,966758,991321]],["copy-to-clipboard",[258205]],["copy-to-clipboard>toggle-selection",[876026]],["core-js-pure",[103107,103339,114407,118560,120990,12759,145412,151859,167878,169640,171391,188366,194094,20560,207845,227607,227906,234303,239218,251954,258224,25884,260437,277064,277389,278892,281378,300024,303606,305727,322167,324522,330035,330636,347599,35086,353883,356579,360330,361546,370579,376588,400874,407322,413491,425440,42848,431842,445047,44943,464270,465210,468876,485365,48724,493823,498293,508591,522818,534096,536708,54840,550184,55696,576773,587510,604916,613408,644976,646878,652078,654273,655559,660948,662482,665216,665580,666050,673319,685672,692487,702630,703066,719418,739256,745597,747440,748841,752223,757537,76589,765917,776008,782214,785151,785818,792385,798491,807583,820394,821049,828095,850958,856768,873303,875224,876763,878832,884024,885109,892910,895202,899114,907471,916872,928937,933068,948638,961964,968682,974770,977075,978775,985456]],["cron-parser",[205227,212712,310998,418605,433256,439869,44598,495081,528063,582032]],["crypto-browserify",[325914,554365]],["crypto-browserify>browserify-cipher",[589534,647133]],["crypto-browserify>browserify-cipher>browserify-des",[213314,769094,838705,87289]],["crypto-browserify>browserify-cipher>browserify-des>des.js",[104109,181690,226565,398216,434961,609466,609652,624295,699112,731279,762931,911426]],["crypto-browserify>browserify-cipher>evp_bytestokey",[406869,626238]],["crypto-browserify>browserify-sign",[136066,184715,184715,184715,184715,184715,184715,184715,210639,229144,370063,373124,499691,543294,629953,661841,661841,661841,661841,661841,661841,661841,750771,786493]],["crypto-browserify>browserify-sign>readable-stream",[146351,19341,207368,24961,34862,348815,389274,400143,423506,440559,482435,484145,49634,597375,691350,728536,85840,954630]],["crypto-browserify>browserify-sign>readable-stream>isarray",[333311,828544]],["crypto-browserify>browserify-sign>readable-stream>safe-buffer",[228612,639389]],["crypto-browserify>browserify-sign>readable-stream>string_decoder",[161690,813931]],["crypto-browserify>browserify-sign>readable-stream>string_decoder>safe-buffer",[68876,791641]],["crypto-browserify>create-ecdh",[65084,966069]],["crypto-browserify>create-hmac",[209475,812935,889832,954968]],["crypto-browserify>diffie-hellman",[432433,487876,53365,53365,53365,53365,53365,53365,53365,678158,705123,746787,7702,837063]],["crypto-browserify>diffie-hellman>miller-rabin",[183009,434884]],["crypto-browserify>pbkdf2",[2216,303271,428172,522749,696696,80105,80295,85317,86900,887331,910166,952964]],["crypto-browserify>pbkdf2>create-hash",[205939,396674,484895,533972]],["crypto-browserify>pbkdf2>ripemd160",[652176,719133]],["crypto-browserify>pbkdf2>ripemd160>hash-base",[552081,571210]],["crypto-browserify>public-encrypt",[139006,277769,288869,353663,372704,574303,576758,584160,710908,8891,889634,97677]],["crypto-browserify>public-encrypt>browserify-rsa",[172788,494167]],["crypto-browserify>public-encrypt>parse-asn1",[199968,392140,502553,657421,756021,784517,890535,890535,890535,890535,890535,890535,890535,905318,910026,996481]],["crypto-browserify>public-encrypt>parse-asn1>asn1.js",[121098,139067,199503,208103,25932,404132,421105,42905,502048,509011,528754,540274,542561,561813,571735,597323,600205,61716,630692,728554,746236,784994,8083,818286,853593,933023,954382,964662]],["crypto-browserify>randombytes",[62174,883369]],["crypto-browserify>randomfill",[938026,96103]],["currency-formatter",[105291,14644,160041,187270,758533,758533,758533,758533,758533,841452,888624,888624,888624,888624,888624,925051]],["currency-formatter>accounting",[241927,946836]],["currency-formatter>locale-currency",[531208,700534,789077,802055]],["deep-freeze-strict",[317764,627685]],["dompurify",[88174]],["eslint-plugin-react>array-includes>is-string",[118857]],["eslint-plugin-react>array-includes>math-intrinsics",[304569,439486,462667,463028,570615,608107,662346,682992,692337,742296,745689,779452,877e3,939663,963442,96533]],["eslint-plugin-react>es-iterator-helpers>has-property-descriptors",[18839,584368]],["eslint-plugin-react>es-iterator-helpers>has-proto>dunder-proto",[76359,826936]],["eslint-plugin-react>hasown",[704149,810364]],["eslint>ajv",[109455,139792,146789,160900,160908,181169,22840,311483,351368,385673,386041,399783,432165,441643,46280,465692,485510,513315,52163,536262,537395,547293,556499,559436,579407,588225,598054,604333,61161,655827,730478,817839,818119,824281,842794,863282,865495,905255,909501,912348,939992,982794]],["eslint>ajv>json-schema-traverse",[30541]],["eslint>fast-deep-equal",[170210,170210,932993]],["eslint>json-stable-stringify-without-jsonify",[559918]],["eth-chainlist",[511445,654063]],["eth-ens-namehash",[206422,558791]],["eth-ens-namehash>idna-uts46-hx",[122252,593891,683712,870019]],["eth-ens-namehash>idna-uts46-hx>punycode",[33245,465768]],["eth-ens-namehash>js-sha3",[227864,617375]],["eth-lattice-keyring",[952149]],["eth-lattice-keyring>@ethereumjs/util",[131149,174743,179264,430793,439138,450906,507597,554335,586527,622779,752653,790569,827649,953807,986280]],["eth-lattice-keyring>@ethereumjs/util>@ethereumjs/rlp",[621952]],["eth-lattice-keyring>@ethereumjs/util>ethereum-cryptography",[347794,592314,592781]],["eth-lattice-keyring>@ethereumjs/util>ethereum-cryptography>@noble/curves",[119428,119968,179401,450927,479374,83071,860803]],["eth-lattice-keyring>@ethereumjs/util>ethereum-cryptography>@noble/hashes",[127207,142176,361558,529766,583378,669609,715738,799524]],["eth-lattice-keyring>@ethereumjs/util>micro-ftch",[203639,879158]],["eth-lattice-keyring>gridplus-sdk",[879893]],["eth-lattice-keyring>gridplus-sdk>@ethereumjs/rlp",[16740,622981]],["eth-lattice-keyring>gridplus-sdk>aes-js",[496439,972828]],["eth-lattice-keyring>gridplus-sdk>bignumber.js",[365514,616649]],["eth-lattice-keyring>gridplus-sdk>bs58check",[474878,610304]],["eth-lattice-keyring>gridplus-sdk>cbor",[178783,363109,366230,378612,457912,523374,571022,62656,676204,802575,871634,875424,877262]],["eth-lattice-keyring>gridplus-sdk>cbor-bigdecimal",[845384]],["eth-lattice-keyring>gridplus-sdk>cbor>nofilter",[903011]],["eth-lattice-keyring>gridplus-sdk>crc-32",[944285]],["eth-lattice-keyring>gridplus-sdk>ox",[227593,672368,756542,783926,813419,83634,839404,843652,969079]],["eth-lattice-keyring>gridplus-sdk>secp256k1",[595409,616671,663367]],["eth-lattice-keyring>gridplus-sdk>zod",[105324,110555,12864,142633,147313,1482,151243,151411,177138,185201,191617,192578,207501,21552,217552,237255,288132,288185,291925,307154,307400,351848,363801,400610,404972,41781,426578,428744,440392,441776,467730,487593,499052,50364,50520,522092,52513,5344,541788,560250,564157,573325,589378,637727,652352,657936,658563,678785,686146,691039,723837,735342,735710,742289,747625,789236,792908,794795,801201,802943,824701,83311,859237,859685,883567,890796,891933,898097,90549,937970,985695,985893,986816,988355]],["eth-lattice-keyring>rlp",[597577]],["eth-method-registry",[243922,243922,243922,243922,243922,260406,432999,662176,852032,852032,852032,852032,852032,917370]],["eth-method-registry>@metamask/ethjs-contract",[149490,171151,22205,304931,679598,814390]],["eth-method-registry>@metamask/ethjs-contract>@metamask/ethjs-filter",[724381,9590]],["eth-method-registry>@metamask/ethjs-contract>@metamask/ethjs-util",[820764,854571]],["eth-method-registry>@metamask/ethjs-contract>ethjs-abi",[43470,452332,814363,889857]],["eth-method-registry>@metamask/ethjs-contract>ethjs-abi>number-to-bn",[545984,55795]],["eth-method-registry>@metamask/ethjs-query",[700457,883348]],["eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format",[407843,95618]],["eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>ethjs-schema",[613122,613122,613122,613122,613122,938438]],["eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>is-hex-prefixed",[414841,433028]],["eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>strip-hex-prefix",[341529,646944]],["eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-rpc",[46392,482131]],["eth-method-registry>@metamask/ethjs-query>promise-to-callback",[555821,587668]],["eth-method-registry>@metamask/ethjs-query>promise-to-callback>is-fn",[754084,948405]],["eth-method-registry>@metamask/ethjs-query>promise-to-callback>set-immediate-shim",[408243,859550]],["ethereum-cryptography",[159084,4007]],["ethereumjs-util",[134666,260161,328669,362242,467537,472431,475168,481899,482062,500520,512477,527514,567856,57111,609919,671352,701181,7201,738955,756854,801305,818896,822020,850844]],["ethereumjs-util>bn.js",[298495,461532]],["ethereumjs-util>create-hash",[311953,765236,825936,906989]],["ethereumjs-util>create-hash>cipher-base",[372024,554885]],["ethereumjs-util>create-hash>md5.js",[618979,689828]],["ethereumjs-util>create-hash>md5.js>hash-base",[368942,943779]],["ethereumjs-util>create-hash>md5.js>hash-base>readable-stream",[138273,144684,160302,269826,271873,295891,348143,377502,388078,399348,400525,503288,531483,555963,556543,614793,644997,646997,653790,696310,700460,703581,708830,727408,757227,789326,877081,909868,938792,973505]],["ethereumjs-util>create-hash>ripemd160",[67700,777899]],["ethereumjs-util>create-hash>ripemd160>hash-base",[346203,571642]],["ethereumjs-util>create-hash>ripemd160>hash-base>readable-stream",[172368,285643,366234,379370,409345,423684,43604,438430,446872,462220,493940,508079,516851,542298,551538,567434,605971,63822,672997,679445,682597,686967,723865,728171,816462,816782,900663,946039,952405,972431]],["ethereumjs-util>ethereum-cryptography",[110404,263109,357147,492315,496988,894002,95453,988970]],["ethereumjs-util>ethereum-cryptography>browserify-aes",[104667,120362,128441,160855,166623,194324,227691,24625,29628,310542,328328,36685,412627,422535,425693,440057,445506,496770,521195,522302,52778,564143,564395,589543,589543,589543,589543,589543,589543,589543,626837,626996,652708,699211,73708,766738,787881,825934,948188,958896]],["ethereumjs-util>ethereum-cryptography>browserify-aes>buffer-xor",[64679,820382]],["ethereumjs-util>ethereum-cryptography>bs58check",[283092,387887,388962,767265]],["ethereumjs-util>ethereum-cryptography>bs58check>bs58",[411447,434124]],["ethereumjs-util>ethereum-cryptography>keccak",[188166,2560,288841,289124,399137,527441,599140,655949,750345,877926,883926,987323]],["ethereumjs-util>ethereum-cryptography>keccak>readable-stream",[141293,172721,234258,234549,236194,261453,364924,418218,43819,450640,45304,519857,527114,535004,546544,571099,611239,618502,634352,7176,722326,731291,740257,751113,75205,770465,779550,817375,893883,972964]],["ethereumjs-util>ethereum-cryptography>secp256k1",[139216,173156,524053,634699,667525,670816]],["ethereumjs-util>rlp",[138403,724840]],["ethers",[164293,21543,528824,794947,863901,898768]],["ethers>@ethersproject/abstract-provider",[120883,211701,445174,721768]],["ethers>@ethersproject/abstract-signer",[230706,320760,654687,659701]],["ethers>@ethersproject/address",[317262,45988,498871,998381]],["ethers>@ethersproject/base64",[307335,384786,880138,893747]],["ethers>@ethersproject/basex",[529193,873202]],["ethers>@ethersproject/constants",[101866,123039,227151,27869,44399,738178,885644,965659]],["ethers>@ethersproject/hash",[130488,151353,234299,248528,252953,407015,410943,412718,460094,475953,578030,580813,603345,79978,815496,886384,896313,974082]],["ethers>@ethersproject/json-wallets",[10921,110781,141830,156057,37426,459908,580226,585497,611720,649603,749805,778052]],["ethers>@ethersproject/json-wallets>aes-js",[144725,302968]],["ethers>@ethersproject/json-wallets>scrypt-js",[305583,587226]],["ethers>@ethersproject/keccak256",[283449,453002]],["ethers>@ethersproject/logger",[329882,697489,795733,851298]],["ethers>@ethersproject/networks",[332071,366639,484058,948074]],["ethers>@ethersproject/pbkdf2",[25643,424913]],["ethers>@ethersproject/properties",[338777,599317,830724,990744]],["ethers>@ethersproject/random",[247023,401282,4058,604816,774575,862331,942107,997866]],["ethers>@ethersproject/rlp",[603988,820707,864089,990142]],["ethers>@ethersproject/sha2",[116409,314693,323064,429146,451058,600141,75056,805929]],["ethers>@ethersproject/sha2>hash.js",[105962,132485,179206,225300,233827,283376,303286,344805,387824,438047,439794,466610,567879,57764,587418,610111,80193,816721,864269,88054,935732,95065,957289,970813]],["ethers>@ethersproject/signing-key",[234380,255468,608111,629441,659946,823777]],["ethers>@ethersproject/solidity",[244921,543716,743720,911877]],["ethers>@ethersproject/strings",[116944,340519,465085,66393,687166,745124,782665,795768,855040,936523]],["ethers>@ethersproject/units",[202520,315087,471253,91170]],["ethers>@ethersproject/wallet",[309353,853669,923412,979240]],["ethers>@ethersproject/web",[213497,254712,465246,55410,699423,800395]],["ethers>@ethersproject/wordlists",[119054,289311,400906,489572,760345,792456,948339,995917]],["extension-port-stream",[250413,283079,283079,284896,48050,48050,770467,770467,803058,803058,895286,969581]],["fast-json-patch",[583955,614020,713905,793403]],["fast-json-stable-stringify",[134899,323260]],["fuse.js",[863985]],["gulp>vinyl-fs>object.assign",[108822,302547,461066,724264,7337,983725]],["he",[106115]],["https-browserify",[301126,965339]],["human-standard-token-abi",[8858,944211]],["humanize-duration",[477355]],["immer",[115691,115691,149501,319222,696906,92365,950515,950515]],["ip-regex",[198465,357910]],["jest-canvas-mock>moo-color>color-name",[469804,865747]],["jsdom>form-data>es-set-tostringtag>has-tostringtag",[197300,520737]],["lightweight-charts",[194859]],["lightweight-charts>fancy-canvas",[128943,243582,418818,443436,631652]],["localforage",[368717,544654]],["lodash",[104045,108041,109528,112437,114787,11604,11616,122080,122368,124162,127750,133527,133630,135471,136011,13645,136467,136471,137234,138115,145831,146498,14786,15361,162389,164325,165238,166136,168474,169811,170906,171118,171577,174506,175458,184084,185971,186049,186265,188312,196025,197614,202665,212003,213676,21937,223116,225953,236872,23879,239930,241297,241421,245780,247742,247835,250846,254517,255991,257776,260153,260393,261031,261432,267558,267642,271916,272175,27390,275044,275159,276617,279177,280621,281657,283238,284431,286210,289577,29025,295215,296e3,298730,302407,303922,305590,308731,309292,310326,311588,319805,323304,323360,328821,329778,331924,33586,337087,338971,339886,342073,347302,358633,361178,365563,366931,369940,371259,372721,376972,37766,377784,378768,383565,384714,386042,38620,392515,394939,396502,402516,403448,408798,418788,422966,423,423679,428926,433702,433752,433789,436820,438993,439107,440477,454001,456884,456895,456895,459722,461663,462732,463851,465022,467343,46751,469896,471378,47548,476031,477765,481585,481803,484412,485063,487091,492973,494319,496246,497781,498256,500610,502503,504273,504559,505062,507307,508394,510185,513194,513580,516534,517141,522306,524621,52547,532006,536076,547269,553939,55422,556600,55750,558909,563252,564009,566425,567069,576629,579481,580484,58095,586053,590267,592557,602190,605271,606144,616279,616685,618431,619507,621923,623755,629352,630748,631123,631293,631328,633411,64027,641229,646272,647294,653160,653538,653552,655676,658647,660966,665681,665697,665940,667537,668205,671945,674312,679571,68055,682329,685209,685544,690007,692677,693608,695038,697058,699180,70028,700365,702879,703623,704597,706892,709499,71038,710858,711744,721248,722604,726804,726927,72890,729875,72999,733395,733693,734277,735548,740036,743714,744305,749347,755389,75570,756305,756483,758387,760697,760824,764347,766570,767785,769200,771366,771899,771954,775138,782268,782784,786045,786752,789007,794238,799648,806927,807822,810914,811255,813523,821432,822539,826448,828974,830728,831939,832771,833325,834725,835792,836760,837054,841476,844065,851077,851099,855675,856549,857178,859340,859340,859564,861862,862430,863344,867029,868080,868916,871429,871614,873126,873198,891013,893608,894995,89524,896540,897579,902706,905621,909440,910005,91158,912220,914506,915186,915320,919816,920277,921849,92473,927445,928442,928680,928863,931579,933290,936218,939132,939690,944880,945343,946985,947365,948312,951867,953568,961475,966382,971279,971795,975932,978696,980341,983963,984180,984271,986377,987137,987173,989410,991966,995922,997080,997225,998084]],["loglevel",[171097,171097,681050,681050]],["lottie-web",[908216]],["luxon",[122552,122552,138292,138292,14631,14631,208570,208570,210164,210164,232712,232712,263496,263496,283707,283707,305921,316244,316244,317588,317588,347022,347022,352134,352134,360569,360569,392134,392134,417476,419186,419186,442525,442525,446655,446655,451798,451798,493104,493104,512986,512986,525037,525037,597054,597054,600473,600473,603476,603476,640846,640846,686333,686333,695358,695358,731318,731318,750628,750628,774810,774810,775158,775158,78565,78565,794204,794204,821213,821213,831022,831022,835060,835060,835203,835203,85013,85013,868766,868766,891728,891728,912276,912276,925752,925752,938102,938102,948972,948972,951906,951906,961520,961520,984381,984381,991213,991213]],["mocha>ms",[134281,254660,254660]],["mocha>yargs-unparser>is-plain-obj",[119552]],["mockttp>@httptoolkit/subscriptions-transport-ws>symbol-observable",[242237,795713,933634,992594]],["mockttp>express>qs",[169116,185960,315677,498449,556189,579775,717698,770603,80776,90124]],["mockttp>express>safe-buffer",[495670,495670,677197,677197]],["nanoid",[250653,531589]],["nock>debug",[465273,617648,683075,683075,952574,952574]],["openai>abort-controller",[113795,113795,581808,581808]],["path-browserify",[386023]],["pify",[182678]],["process",[208835,208835,208835,378326,378326]],["prop-types",[173442,557789,787332,815223,883107,991606]],["psl",[153782,708648]],["pumpify>inherits",[509847,509847,985738,985738]],["punycode",[478759,844744]],["qrcode-generator",[929736]],["qrcode.react",[174799]],["react",[23591,276592,336620,694737,740770,860012]],["react-beautiful-dnd",[556653]],["react-beautiful-dnd>css-box-model",[200635]],["react-beautiful-dnd>css-box-model>tiny-invariant",[387325]],["react-beautiful-dnd>memoize-one",[62147]],["react-beautiful-dnd>raf-schd",[930197]],["react-beautiful-dnd>use-memo-one",[214897]],["react-chartjs-2",[173127]],["react-compiler-runtime",[303280,844129]],["react-devtools-core",[38588]],["react-dom",[1159,421522,54490,879505]],["react-dom>scheduler",[285234,355808,628313,707611]],["react-focus-lock",[124676,171702,304417,59129,679770,921718,977522]],["react-focus-lock>focus-lock",[130680,135719,153956,176839,296640,341413,360116,365187,367975,417071,578063,653567,664882,697295,716734,750025,780392,826111,837793,906089,997295]],["react-focus-lock>react-clientside-effect",[132165]],["react-focus-lock>use-callback-ref",[334392,415976,989992]],["react-focus-lock>use-sidecar",[886509]],["react-hot-toast",[638891]],["react-hot-toast>goober",[656304]],["react-idle-timer",[282382]],["react-markdown",[66117,909295,966680,973839]],["react-markdown>comma-separated-tokens",[142527]],["react-markdown>property-information",[109794,136933,222985,287738,293780,403493,403939,489890,625821,651420,709064,709064,709064,709064,709064,713726,815182,887583,897558,918358,927244,95526,993601]],["react-markdown>react-is",[287916,848688]],["react-markdown>remark-parse",[11815]],["react-markdown>remark-parse>mdast-util-from-markdown",[284865,839200]],["react-markdown>remark-parse>mdast-util-from-markdown>mdast-util-to-string",[350350]],["react-markdown>remark-parse>mdast-util-from-markdown>micromark",[115271,122266,129245,13320,144508,147528,156518,158366,160413,166022,167141,191006,236757,255771,300725,32735,345752,350100,367096,369e3,386920,387601,415431,429198,432225,434122,465465,472696,50096,50571,505862,513233,517015,542008,55976,588891,596678,619258,619473,626280,646592,667890,677964,678462,68733,703367,725077,749567,754388,757024,763528,779357,784573,804392,835101,852994,857909,861137,877216,89161,913200,91494,920522,935714,942864,961766,970745,971206,971933,993242,995783]],["react-markdown>remark-rehype",[607537]],["react-markdown>remark-rehype>mdast-util-to-hast",[127017,130453,157984,191532,195532,215432,235812,247600,281038,317058,361014,370310,467157,532167,540226,542795,55227,56788,571047,577504,645553,646177,658367,694268,695298,712147,866355,868166,943308,964922]],["react-markdown>remark-rehype>mdast-util-to-hast>mdurl",[590387]],["react-markdown>remark-rehype>mdast-util-to-hast>unist-builder",[7900]],["react-markdown>remark-rehype>mdast-util-to-hast>unist-util-generated",[602721]],["react-markdown>remark-rehype>mdast-util-to-hast>unist-util-position",[679975]],["react-markdown>space-separated-tokens",[127668]],["react-markdown>style-to-object",[230916]],["react-markdown>style-to-object>inline-style-parser",[395196]],["react-markdown>unified",[286837]],["react-markdown>unified>bail",[370001]],["react-markdown>unified>extend",[203585]],["react-markdown>unified>is-buffer",[287094]],["react-markdown>unified>trough",[652804]],["react-markdown>unist-util-visit",[498679]],["react-markdown>unist-util-visit>unist-util-is",[498559]],["react-markdown>unist-util-visit>unist-util-visit-parents",[776279,949742]],["react-markdown>vfile",[461651,621468]],["react-markdown>vfile>is-buffer",[444576]],["react-markdown>vfile>replace-ext",[68215]],["react-markdown>vfile>unist-util-stringify-position",[296107]],["react-markdown>vfile>vfile-message",[166301]],["react-popper",[646948,897908]],["react-popper>react-fast-compare",[101875]],["react-redux",[132837,160697,169835,176578,193183,196108,202818,228907,23106,235140,263695,291331,314102,314701,322489,369148,421859,470995,473584,48084,525300,52906,541328,5637,578600,601618,62629,630119,684723,691857,701844,721075,733602,738790,745865,772362,77364,872169,956152,966284]],["react-redux>hoist-non-react-statics",[339394,779833]],["react-redux>hoist-non-react-statics>react-is",[113132,29065,337392,810621]],["react-redux>react-is",[128570,457869,828750,924865]],["react-router-dom",[994112]],["react-router-dom>@remix-run/router",[682660]],["react-router-dom>react-router",[107495]],["react-simple-file-input",[742431]],["react-syntax-highlighter>refractor>parse-entities",[512920]],["react-tippy",[971180]],["react-tippy>popper.js",[975427]],["react-toggle-button",[490926]],["react-transition-group",[131350,284003,639130,829556,84954,936137,996331]],["react-transition-group>dom-helpers",[475843,815834,819347]],["react>object-assign",[580513,858524]],["readable-stream",[153089,153089,181536,181536,194535,194535,22250,22250,252334,252334,252859,252859,259290,259290,261069,261069,294855,294855,338568,338568,425493,425493,425934,425934,443305,443305,44565,44565,448492,448492,449219,449219,452547,452547,464812,464812,485697,485697,494639,494639,548444,548444,568577,568577,586805,586805,588847,588847,602416,602416,613318,613318,631222,631222,632914,632914,68266,68266,683024,683024,699960,699960,703102,703102,708566,708566,730636,730636,73701,73701,754857,754857,761124,761124,769584,769584,770587,770587,777352,777352,809090,809090,816718,816718,827525,827525,831171,831171,837911,837911,868387,868387,895890,895890,900457,900457,930607,930607,978529,978529]],["readable-stream-2>core-util-is",[711510,734263]],["readable-stream-2>process-nextick-args",[102393,951712]],["redux",[60416,781107]],["redux-thunk",[411596,488961]],["remote-redux-devtools",[120430,120443,272386,398548,417589,520163,712044,821125]],["remote-redux-devtools>jsan",[151109,214772,341696,425053,427767,484280,769126,888547,965556,976999]],["remote-redux-devtools>redux-devtools-core",[172251,464033,650496,778624,920936,952353]],["remote-redux-devtools>redux-devtools-core>get-params",[197263,31908]],["remote-redux-devtools>redux-devtools-core>nanoid",[659269,987968]],["remote-redux-devtools>redux-devtools-core>remotedev-serialize",[205061,274996,34802,464435,559720,625641]],["remote-redux-devtools>redux-devtools-instrument",[217867,527526]],["remote-redux-devtools>rn-host-detect",[382693,653154]],["remote-redux-devtools>socketcluster-client",[105123,200509,280959,336672,46337,672552,686524,701487,729213,844684,930487,94862,963198,967124]],["remote-redux-devtools>socketcluster-client>buffer",[627940,661655]],["remote-redux-devtools>socketcluster-client>clone",[196027,430638]],["remote-redux-devtools>socketcluster-client>component-emitter",[311812,372675]],["remote-redux-devtools>socketcluster-client>linked-list",[262580,407096,497509,759067]],["remote-redux-devtools>socketcluster-client>querystring",[29941,368576,509196,538628,554315,676013]],["remote-redux-devtools>socketcluster-client>sc-channel",[608408,891709]],["remote-redux-devtools>socketcluster-client>sc-errors",[222755,520309,559530,601342]],["remote-redux-devtools>socketcluster-client>sc-formatter",[38652,918851]],["remote-redux-devtools>socketcluster-client>uuid",[107216,192925,316263,513880,605920,648025,675081,751632,905155,998316]],["reselect",[320826,491616]],["sass-embedded>varint",[136914,182884,562618,78542]],["semver",[102998,103370,130698,143902,148533,159585,197544,212669,213832,220692,223550,230370,231148,23533,24503,248391,250377,256030,261200,275905,279024,282429,297891,300736,315317,321564,330975,3310,343546,348400,36974,389193,400386,444259,458014,464838,466097,467260,469878,481665,502116,520364,523337,526710,539237,547847,563167,568925,588412,589551,599249,601198,605657,606005,618315,620631,630655,645178,661824,673188,675323,677238,685987,692636,696027,712800,71608,74207,771932,783212,801015,829373,838869,839933,843432,846768,869544,872547,884499,887195,908975,9090,917098,919006,927927,930980,934487,944893,980803,993225]],["stream-browserify",[594950,985631]],["stream-browserify>readable-stream",[109279,124413,207664,249192,284417,305685,311802,312964,32544,464002,500040,522422,525412,52799,588091,69755,699075,715374,719265,765283,794353,836603,864599,903300,93530,969524,982626,994407]],["stream-http",[162465,270320,482901,683392,802719,899161,947198,99248]],["stream-http>builtin-status-codes",[535522,538673]],["stream-http>readable-stream",[113306,184437,189546,193050,201511,23086,324940,331753,363357,382647,408375,410939,438859,493781,50326,512565,626160,657508,665564,719184,748454,786999,790540,790745,81802,823306,874757,891549,930722,988137]],["string.prototype.matchall>call-bind",[567943,705035,870428,908492]],["string.prototype.matchall>call-bind>call-bind-apply-helpers",[106983,161613,186343,26796,569214,635101,647304,653002,723547,763902,870079,873110]],["string.prototype.matchall>call-bind>es-define-property",[42678,861807]],["string.prototype.matchall>call-bind>set-function-length",[530974,874449]],["string.prototype.matchall>call-bound",[270335,727164]],["string.prototype.matchall>define-properties",[624233,919684]],["string.prototype.matchall>define-properties>define-data-property",[316328,562089]],["string.prototype.matchall>es-abstract>array-buffer-byte-length",[664167]],["string.prototype.matchall>es-abstract>available-typed-arrays",[855401,94121]],["string.prototype.matchall>es-abstract>es-to-primitive>is-symbol",[613340]],["string.prototype.matchall>es-abstract>get-proto",[193624,296369,487929,622892,685451,744104]],["string.prototype.matchall>es-abstract>is-array-buffer",[78062]],["string.prototype.matchall>es-abstract>is-callable",[714961,76176]],["string.prototype.matchall>es-abstract>is-regex",[129042,969219]],["string.prototype.matchall>es-abstract>is-set",[275840]],["string.prototype.matchall>es-abstract>is-shared-array-buffer",[610558]],["string.prototype.matchall>es-abstract>object-inspect",[427195,75518]],["string.prototype.matchall>es-abstract>safe-regex-test",[316702,92025]],["string.prototype.matchall>es-abstract>stop-iteration-iterator",[181996]],["string.prototype.matchall>es-abstract>typed-array-buffer",[572815,813364]],["string.prototype.matchall>es-abstract>typed-array-length>possible-typed-array-names",[267058,676397]],["string.prototype.matchall>es-abstract>unbox-primitive>has-bigints",[733838]],["string.prototype.matchall>es-errors",[123456,29270,331300,382711,444699,492449,529354,542599,592005,602240,701026,782051,998630,999363]],["string.prototype.matchall>es-object-atoms",[428557,588684]],["string.prototype.matchall>get-intrinsic",[399154,933]],["string.prototype.matchall>get-intrinsic>async-function",[264913,779198]],["string.prototype.matchall>get-intrinsic>async-generator-function",[848185,998538]],["string.prototype.matchall>get-intrinsic>generator-function",[359060,735833]],["string.prototype.matchall>gopd",[114642,377379,768613,809614]],["string.prototype.matchall>has-symbols",[160055,432088,480278,694053]],["string.prototype.matchall>internal-slot",[228431]],["string.prototype.matchall>regexp.prototype.flags",[167986,330037,739552,85627]],["string.prototype.matchall>set-function-name",[81814]],["string.prototype.matchall>set-function-name>functions-have-names",[645102]],["string.prototype.matchall>side-channel",[114231,800360]],["string.prototype.matchall>side-channel>side-channel-list",[547412,592227]],["string.prototype.matchall>side-channel>side-channel-map",[344459,651190]],["string.prototype.matchall>side-channel>side-channel-weakmap",[160534,176959]],["terser>source-map-support>buffer-from",[734479]],["ts-mixer",[227662,96481]],["tslib",[770591,92295]],["tweetnacl",[74552,990115]],["unicode-confusables",[531743,531743,531743,531743,531743,540270]],["uri-js",[565e3,925475]],["uuid",[106555,112471,123628,123628,123628,132168,16478,282003,299896,301170,38401,400872,485791,506589,516074,576324,585925,605078,620897,621501,659008,659008,659008,707602,720579,724966,731163,739070,761366,834669,834669,834669,849401,921766,921766,921766,923533,951545,951545,951545]],["viem",[1054,113464,120472,132844,13662,151844,191805,191824,203917,212479,220332,255573,264232,27153,271723,283405,306605,30888,338842,345173,347862,349282,426943,466978,480239,492688,506576,525638,530260,546714,551211,570625,621094,627079,640633,643959,656079,673975,674715,683260,684075,707051,718316,739919,753115,778351,804027,816385,880922,885351,911973,941986,967731]],["viem>abitype",[146485,150706,17047,173179,246690,283116,291216,345489,441602,633441,64090,749845,864721]],["wait-on>axios",[132519,138428,17975,183401,196434,235935,247769,2556,260798,269126,272145,279845,302569,307443,329788,337049,337521,347359,35829,365459,374258,405386,423956,435085,443032,447923,451360,456048,47793,516138,527358,561903,573038,577145,621558,627273,652455,653978,685727,686914,727629,732582,736027,738874,743479,757315,771027,776451,793963,933203]],["wait-on>rxjs",[181684,246511,284905,288855,330355,333101,352984,386675,455485,473262,526292,534931,545828,598869,668048,733160,861952,924791]],["watchify>xtend",[445334,457827]],["web-vitals",[811870]],["webextension-polyfill",[392248,392248,413279,413279]],["webpack-cli>fastest-levenshtein",[70144]],["webpack>events",[780063,780063,998088,998088]]],e.unenforceable=[121455,20168,20168,20168,20168,20168,20168,20168,201783,201783,201783,201783,201783,236305,236305,236305,245672,245672,245672,245672,245672,245672,245672,245672,337994,337994,337994,337994,337994,337994,337994,337994,343966,343966,343966,343966,343966,343966,343966,343966,371173,383972,383972,383972,383972,383972,383972,383972,383972,400495,400495,400495,400495,400495,400495,400495,400495,439181,440830,440830,440830,440830,440830,440830,446179,490513,490513,490513,490513,490513,490513,490513,490513,492752,531854,531854,531854,531854,531854,531854,531854,531854,588776,588776,588776,588776,588776,588776,588776,588776,619200,623661,623661,623661,623661,623661,623661,623661,623661,638581,638581,638581,638581,638581,638581,638581,638581,639266,639266,639266,639266,639266,639266,639266,639266,667544,667544,667544,667544,667544,667544,667544,667544,685066,685066,685066,685066,685066,685066,685066,685066,68724,68724,68724,68724,68724,68724,705444,715050,715050,715050,715050,715050,715050,715050,715050,733258,733258,733258,733258,733258,733258,733258,733258,744643,744643,744643,744643,744643,744643,744643,744643,74754,762634,762634,762634,762634,762634,762634,762634,762634,792981,792981,792981,792981,792981,792981,792981,792981,794832,794832,794832,801874,801874,801874,833028,901409,901409,901409,901409,901409,901409,901409,901409,902731,902731,902731,902731,902731,950514,950514,950514,950514,950514,950514,950514,960548,960548,960548,960548,960548,960548,980564,980564,980564,980564,980564,980564,980564,980564,999154,999154,999154],e.ctxm=[],e.kch=[110,1105,1122,1290,1296,1309,133,1331,1391,1422,1491,1507,1522,1523,1598,1646,166,1684,1728,1768,1791,1818,1826,185,1863,1864,1887,2083,2118,2160,2186,2189,2203,2213,2215,229,2430,2445,2449,2501,2514,2584,2638,2664,2669,2710,2721,2747,2776,285,2962,3139,3186,3210,3375,339,3400,3404,343,3602,3638,3740,3779,3785,3809,3881,3885,3931,3956,4016,4052,407,4073,4113,418,4186,4243,425,4258,427,4274,4294,4307,4323,4377,4480,4520,4549,4579,4593,4594,46,461,463,4634,4753,4781,483,4842,4859,5087,5098,5151,5175,5250,5271,5297,5407,5458,5530,5609,5616,5657,5671,5796,5864,5927,6023,6053,6078,6115,614,6141,6209,6336,634,6358,6401,6556,659,6622,6649,6660,670,6802,6828,6906,7064,7091,7145,7160,7178,7219,7236,7449,7497,7547,7614,7622,7651,7755,78,7899,7962,7980,7998,8015,8034,8063,8093,8102,8160,8264,836,8364,8427,8452,8528,8650,8693,8734,8789,8792,8811,887,891,8927,8935,8979,8994,9038,904,9046,9060,9121,9165,9177,9186,9232,9277,9281,9313,9354,9600,9674,9689,9737,9778,9807,9861,9949,9957],e.externals={},e.options={lockdown:{consoleTaming:"unsafe",errorTaming:"unsafe",errorTrapping:"none",localeTaming:"unsafe",overrideTaming:"severe",reporting:"none",stackFiltering:"verbose"},scuttleGlobalThis:{enabled:!0,exceptions:["window","Proxy","toString","getComputedStyle","addEventListener","removeEventListener","ShadowRoot","HTMLElement","HTMLFormElement","Element","pageXOffset","pageYOffset","visualViewport","Reflect","Set","Object","navigator","harden","console","WeakSet","Event","EventTarget","Image","fetch","AbortController","OffscreenCanvas","/cdc_[a-zA-Z0-9]+_[a-zA-Z]+/iu","name","performance","parseFloat","innerWidth","innerHeight","Symbol","Math","DOMRect","Number","Array","crypto","Function","Uint8Array","String","Promise","JSON","Date","RegExp","__SENTRY__","appState","extra","stateHooks","sentryHooks","sentry","logEncryptedVault","history","getSelection","opr","devicePixelRatio","ResizeObserver","setTimeout","clearTimeout","webpackChunk"],scuttlerName:"SCUTTLER"}},(()=>{let t={exports:{}};t.exports;let{Object:r,Array:a,Error:s,RegExp:o,Set:n,console:c,Proxy:l,Reflect:i}=globalThis,{assign:m,getOwnPropertyNames:p,getOwnPropertyDescriptor:u,create:h,defineProperty:g}=r,d=function(e,t){return r.getOwnPropertyNames(e).filter(r=>e[r]===t[r]).concat(["Compartment","Error","globalThis"])}(new Compartment().globalThis,globalThis),{isArray:b,from:k}=a,{getPrototypeOf:y}=i,{warn:f}=c;t.exports={scuttle:function(e,t){let r=function(e,t=h(null)){let r={enabled:!0,exceptions:[],scuttlerName:""},a=m(h(null),!0===t?r:t,{scuttlerFunc:(e,t)=>t(e)},{exceptions:(t?.exceptions||r.exceptions).map(e=>(function(e){if(!e.startsWith("/"))return e;let t=e.split("/");return new o(t.slice(1,-1).join("/"),t[t.length-1])})(e))});if(a.scuttlerName){if(!e[a.scuttlerName])throw new s(`LavaMoat - 'scuttlerName' function "${a.scuttlerName}" expected on globalRef.To learn more visit https://github.com/LavaMoat/LavaMoat/pull/462.`);a.scuttlerFunc=e[a.scuttlerName]}return a}(e,t);if(r.enabled){if(!b(r.exceptions))throw new s(`LavaMoat - exceptions must be an array, got ${typeof r.exceptions}`);r.scuttlerFunc(e,e=>(function(e,t=[]){let r=[];(function(e){let t=[],r=e;for(;r&&("object"==typeof r||"function"==typeof r);)t.push(r),r=y(r);return t})(e).forEach(e=>r.push(...p(e)));let a=new n([...d,...t]),c=h(null);r.forEach(t=>{let r,n,{get:i,set:m}={get:function(){throw new s(`LavaMoat - property "${t}" of globalThis is inaccessible under scuttling mode. To learn more visit https://github.com/LavaMoat/LavaMoat/pull/360.`)},set:function(){f(`LavaMoat - property "${t}" of globalThis cannot be set under scuttling mode. To learn more visit https://github.com/LavaMoat/LavaMoat/pull/360.`)}};if(r=a,n=t,k(r).some(e=>"string"==typeof e&&e===n||e instanceof o&&e.test(n)))return;let p=u(e,t);if(p?.configurable===!0)p={configurable:!1,set:m,get:i};else{if(p?.writable!==!0)return;p={configurable:!1,writable:!1,value:new l(c,{getPrototypeOf:i,get:i,set:m})}}g(e,t,p)})})(e,r.exceptions))}}},e.scuttling=t.exports})(),e.policy={resources:{"@babel/runtime":{globals:{regeneratorRuntime:"write"}},"@emotion/react":{globals:{HTMLElement:!0,"document.querySelector":!0},packages:{"@babel/runtime":!0,"@emotion/react>@emotion/cache":!0,"@emotion/react>@emotion/serialize":!0,"@emotion/react>@emotion/use-insertion-effect-with-fallbacks":!0,"@emotion/react>@emotion/utils":!0,"@emotion/react>@emotion/weak-memoize":!0,react:!0,"react-redux>hoist-non-react-statics":!0}},"@emotion/react>@emotion/cache":{globals:{"document.head":!0,"document.querySelectorAll":!0},packages:{"@emotion/react>@emotion/cache>@emotion/memoize":!0,"@emotion/react>@emotion/cache>@emotion/sheet":!0,"@emotion/react>@emotion/cache>stylis":!0,"@emotion/react>@emotion/weak-memoize":!0}},"@emotion/react>@emotion/cache>@emotion/sheet":{globals:{"document.createElement":!0,"document.createTextNode":!0,"document.styleSheets":!0}},"@emotion/react>@emotion/serialize":{packages:{"@emotion/react>@emotion/cache>@emotion/memoize":!0,"@emotion/react>@emotion/serialize>@emotion/hash":!0,"@emotion/react>@emotion/serialize>@emotion/unitless":!0}},"@emotion/react>@emotion/use-insertion-effect-with-fallbacks":{packages:{react:!0}},"@emotion/styled":{packages:{"@babel/runtime":!0,"@emotion/react":!0,"@emotion/react>@emotion/serialize":!0,"@emotion/react>@emotion/use-insertion-effect-with-fallbacks":!0,"@emotion/react>@emotion/utils":!0,"@emotion/styled>@emotion/is-prop-valid":!0,react:!0}},"@emotion/styled>@emotion/is-prop-valid":{packages:{"@emotion/react>@emotion/cache>@emotion/memoize":!0}},"@ensdomains/content-hash>multihashes>multibase>base-x":{packages:{"mockttp>express>safe-buffer":!0}},"@ethereumjs/tx":{packages:{"@ethereumjs/tx>@ethereumjs/common":!0,"@ethereumjs/tx>@ethereumjs/rlp":!0,"@ethereumjs/tx>@ethereumjs/util":!0,"@ethereumjs/tx>ethereum-cryptography":!0}},"@ethereumjs/tx>@ethereumjs/common":{packages:{"@ethereumjs/tx>@ethereumjs/util":!0,"webpack>events":!0}},"@ethereumjs/tx>@ethereumjs/rlp":{globals:{TextEncoder:!0}},"@ethereumjs/tx>@ethereumjs/util":{globals:{"console.warn":!0,fetch:!0},packages:{"@ethereumjs/tx>@ethereumjs/rlp":!0,"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography":!0,"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/curves":!0,"@ethereumjs/tx>ethereum-cryptography>@noble/curves":!0,"webpack>events":!0}},"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0,module:!0},packages:{"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/curves":!0,"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/hashes":!0}},"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/curves":{globals:{TextEncoder:!0},packages:{"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/hashes":!0}},"@ethereumjs/tx>@ethereumjs/util>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0,crypto:!0}},"@ethereumjs/tx>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0,module:!0},packages:{"@ethereumjs/tx>ethereum-cryptography>@noble/hashes":!0}},"@ethereumjs/tx>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0}},"@ethersproject/abi":{globals:{"console.log":!0},packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/constants":!0,"ethers>@ethersproject/hash":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/strings":!0}},"@ethersproject/bignumber":{packages:{"@ethersproject/bytes":!0,"ethereumjs-util>bn.js":!0,"ethers>@ethersproject/logger":!0}},"@ethersproject/bytes":{packages:{"ethers>@ethersproject/logger":!0}},"@ethersproject/contracts":{globals:{setTimeout:!0},packages:{"@ethersproject/abi":!0,"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"@ethersproject/transactions":!0,"ethers>@ethersproject/abstract-provider":!0,"ethers>@ethersproject/abstract-signer":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0}},"@ethersproject/hdnode":{packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"@ethersproject/transactions":!0,"ethers>@ethersproject/basex":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/pbkdf2":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/sha2":!0,"ethers>@ethersproject/signing-key":!0,"ethers>@ethersproject/strings":!0,"ethers>@ethersproject/wordlists":!0}},"@ethersproject/providers":{globals:{WebSocket:!0,clearInterval:!0,clearTimeout:!0,"console.log":!0,"console.warn":!0,setInterval:!0,setTimeout:!0},packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"@ethersproject/providers>bech32":!0,"@ethersproject/transactions":!0,"ethers>@ethersproject/abstract-provider":!0,"ethers>@ethersproject/abstract-signer":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/base64":!0,"ethers>@ethersproject/basex":!0,"ethers>@ethersproject/constants":!0,"ethers>@ethersproject/hash":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/networks":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/random":!0,"ethers>@ethersproject/sha2":!0,"ethers>@ethersproject/strings":!0,"ethers>@ethersproject/web":!0}},"@ethersproject/transactions":{packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/constants":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/rlp":!0,"ethers>@ethersproject/signing-key":!0}},"@google/genai>protobufjs":{globals:{process:!0,setTimeout:!0},packages:{"@google/genai>protobufjs>@protobufjs/aspromise":!0,"@google/genai>protobufjs>@protobufjs/base64":!0,"@google/genai>protobufjs>@protobufjs/codegen":!0,"@google/genai>protobufjs>@protobufjs/eventemitter":!0,"@google/genai>protobufjs>@protobufjs/fetch":!0,"@google/genai>protobufjs>@protobufjs/float":!0,"@google/genai>protobufjs>@protobufjs/path":!0,"@google/genai>protobufjs>@protobufjs/pool":!0,"@google/genai>protobufjs>@protobufjs/utf8":!0,"@google/genai>protobufjs>long":!0}},"@google/genai>protobufjs>@protobufjs/codegen":{globals:{"console.log":!0}},"@google/genai>protobufjs>@protobufjs/fetch":{globals:{XMLHttpRequest:!0},packages:{"@google/genai>protobufjs>@protobufjs/aspromise":!0}},"@google/genai>protobufjs>long":{globals:{"WebAssembly.Instance":!0,"WebAssembly.Module":!0,define:!0}},"@keystonehq/bc-ur-registry-eth":{globals:{"Buffer.from":!0},packages:{"@ethereumjs/tx>@ethereumjs/util":!0,"@keystonehq/bc-ur-registry-eth>@keystonehq/bc-ur-registry":!0,"@metamask/eth-qr-keyring>hdkey":!0,buffer:!0,uuid:!0}},"@keystonehq/bc-ur-registry-eth>@keystonehq/bc-ur-registry":{globals:{Buffer:!0,define:!0},packages:{"@ngraveio/bc-ur":!0,buffer:!0,"ethereumjs-util>ethereum-cryptography>bs58check":!0,tslib:!0}},"@lavamoat/lavadome-react":{globals:{Array:!0,Clipboard:!0,Document:!0,DocumentFragment:!0,Element:!0,Event:!0,EventTarget:!0,Function:!0,JSON:!0,NavigateEvent:!0,NavigationDestination:!0,Node:!0,Number:!0,Object:!0,String:!0,Weakmap:!0,"console.warn":!0,document:!0,navigation:!0},packages:{react:!0}},"@ledgerhq/errors":{globals:{"console.warn":!0}},"@ledgerhq/hw-app-eth":{globals:{"Buffer.alloc":!0,"Buffer.concat":!0,"Buffer.from":!0,"console.warn":!0},packages:{"@ethersproject/abi":!0,"@ethersproject/transactions":!0,"@ledgerhq/errors":!0,"@ledgerhq/hw-app-eth>@ledgerhq/cryptoassets-evm-signatures":!0,"@ledgerhq/hw-app-eth>@ledgerhq/domain-service":!0,"@ledgerhq/hw-app-eth>@ledgerhq/evm-tools":!0,"@ledgerhq/hw-app-eth>@ledgerhq/logs":!0,"@ledgerhq/hw-app-eth>bignumber.js":!0,buffer:!0,"ethers>@ethersproject/rlp":!0,semver:!0,"wait-on>axios":!0}},"@ledgerhq/hw-app-eth>@ledgerhq/domain-service":{packages:{"@ledgerhq/hw-app-eth>@ledgerhq/logs":!0,"wait-on>axios":!0}},"@ledgerhq/hw-app-eth>@ledgerhq/evm-tools":{packages:{"@ledgerhq/hw-app-eth>@ledgerhq/cryptoassets-evm-signatures":!0,"@ledgerhq/hw-app-eth>@ledgerhq/evm-tools>@ledgerhq/live-env":!0,"@metamask/ppom-validator>crypto-js":!0,"ethers>@ethersproject/constants":!0,"ethers>@ethersproject/hash":!0,"wait-on>axios":!0}},"@ledgerhq/hw-app-eth>@ledgerhq/evm-tools>@ledgerhq/live-env":{globals:{"console.warn":!0},packages:{"wait-on>rxjs":!0}},"@ledgerhq/hw-app-eth>@ledgerhq/logs":{globals:{__ledgerLogsListen:"write","console.error":!0}},"@ledgerhq/hw-app-eth>bignumber.js":{globals:{crypto:!0}},"@ledgerhq/hw-transport-webhid":{globals:{"Buffer.from":!0,navigator:!0},packages:{"@ledgerhq/errors":!0,"@ledgerhq/hw-app-eth>@ledgerhq/logs":!0,"@ledgerhq/hw-transport-webhid>@ledgerhq/devices":!0,"@ledgerhq/hw-transport-webhid>@ledgerhq/hw-transport":!0,buffer:!0}},"@ledgerhq/hw-transport-webhid>@ledgerhq/devices":{globals:{"Buffer.alloc":!0,"Buffer.concat":!0},packages:{"@ledgerhq/errors":!0,"@ledgerhq/hw-transport-webhid>@ledgerhq/devices>semver":!0,buffer:!0}},"@ledgerhq/hw-transport-webhid>@ledgerhq/devices>semver":{globals:{"console.error":!0,process:!0},packages:{process:!0}},"@ledgerhq/hw-transport-webhid>@ledgerhq/hw-transport":{globals:{"Buffer.alloc":!0,"Buffer.concat":!0,"Buffer.from":!0,clearTimeout:!0,"console.warn":!0,setTimeout:!0},packages:{"@ledgerhq/errors":!0,"@ledgerhq/hw-app-eth>@ledgerhq/logs":!0,buffer:!0,"webpack>events":!0}},"@metamask/abi-utils":{packages:{"@metamask/superstruct":!0,"@metamask/utils":!0}},"@metamask/account-api":{packages:{"@metamask/keyring-utils":!0}},"@metamask/account-tree-controller":{globals:{"console.warn":!0,setTimeout:!0},packages:{"@metamask/account-api":!0,"@metamask/accounts-controller":!0,"@metamask/base-controller":!0,"@metamask/keyring-api":!0,"@metamask/keyring-controller":!0,"@metamask/profile-sync-controller":!0,"@metamask/snaps-utils":!0,"@metamask/superstruct":!0,"@metamask/utils":!0,"eslint>fast-deep-equal":!0}},"@metamask/accounts-controller":{globals:{"console.warn":!0},packages:{"@metamask/accounts-controller>ethereum-cryptography":!0,"@metamask/keyring-api":!0,"@metamask/keyring-controller":!0,"@metamask/superstruct":!0,"@metamask/utils":!0,uuid:!0}},"@metamask/accounts-controller>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0,module:!0},packages:{"@metamask/accounts-controller>ethereum-cryptography>@noble/hashes":!0}},"@metamask/accounts-controller>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0}},"@metamask/approval-controller":{globals:{"console.info":!0},packages:{"@metamask/base-controller":!0,"@metamask/rpc-errors":!0,nanoid:!0}},"@metamask/assets-controller":{globals:{clearInterval:!0,clearTimeout:!0,"console.error":!0,"fetch.bind":!0,"performance.now":!0,setInterval:!0,setTimeout:!0},packages:{"@ethereumjs/tx>@ethereumjs/util":!0,"@ethersproject/abi":!0,"@ethersproject/providers":!0,"@metamask/assets-controller>bignumber.js":!0,"@metamask/assets-controller>p-limit":!0,"@metamask/assets-controllers":!0,"@metamask/base-controller":!0,"@metamask/client-controller":!0,"@metamask/controller-utils":!0,"@metamask/core-backend":!0,"@metamask/keyring-snap-client":!0,"@metamask/phishing-controller":!0,"@metamask/polling-controller":!0,"@metamask/snaps-utils":!0,"@metamask/utils":!0,"async-mutex":!0,lodash:!0}},"@metamask/assets-controller>bignumber.js":{globals:{crypto:!0}},"@metamask/assets-controller>p-limit":{packages:{"@metamask/assets-controller>p-limit>yocto-queue":!0}},"@metamask/assets-controllers":{globals:{"Intl.NumberFormat":!0,URL:!0,"console.error":!0},packages:{"@ethersproject/contracts":!0,"@ethersproject/providers":!0,"@metamask/account-api":!0,"@metamask/assets-controllers>multiformats":!0,"@metamask/assets-controllers>single-call-balance-checker-abi":!0,"@metamask/controller-utils":!0,"@metamask/keyring-api":!0,"@metamask/utils":!0,"ethereumjs-util>bn.js":!0,reselect:!0}},"@metamask/assets-controllers>multiformats":{globals:{TextDecoder:!0,TextEncoder:!0,"console.warn":!0}},"@metamask/authenticated-user-storage":{packages:{"@metamask/superstruct":!0}},"@metamask/base-controller":{globals:{"console.error":!0},packages:{immer:!0}},"@metamask/bridge-controller":{globals:{URLSearchParams:!0,"console.warn":!0},packages:{"@ethersproject/contracts":!0,"@ethersproject/providers":!0,"@metamask/bridge-controller>@metamask/multichain-network-controller":!0,"@metamask/bridge-controller>bignumber.js":!0,"@metamask/controller-utils":!0,"@metamask/keyring-api":!0,"@metamask/metamask-eth-abis":!0,"@metamask/multichain-network-controller":!0,"@metamask/superstruct":!0,"@metamask/utils":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/constants":!0,lodash:!0,reselect:!0}},"@metamask/bridge-controller>bignumber.js":{globals:{crypto:!0}},"@metamask/chain-agnostic-permission":{packages:{"@metamask/chain-agnostic-permission>@metamask/api-specs":!0,"@metamask/controller-utils":!0,"@metamask/permission-controller":!0,"@metamask/utils":!0,lodash:!0}},"@metamask/claims-controller":{packages:{"@metamask/claims-controller>@metamask/controller-utils":!0}},"@metamask/compliance-controller":{packages:{"@metamask/base-controller":!0,"@metamask/controller-utils":!0,reselect:!0}},"@metamask/controller-utils":{globals:{"Buffer.from":!0,URL:!0,"console.error":!0,fetch:!0,setTimeout:!0},packages:{"@ethersproject/abi":!0,"@metamask/controller-utils>@metamask/ethjs-unit":!0,"@metamask/controller-utils>@spruceid/siwe-parser":!0,"@metamask/utils":!0,buffer:!0,cockatiel:!0,"eslint>fast-deep-equal":!0,"eth-ens-namehash":!0,"ethereumjs-util>bn.js":!0,lodash:!0}},"@metamask/controller-utils>@metamask/eth-query":{packages:{"@metamask/ppom-validator>json-rpc-random-id":!0,"watchify>xtend":!0}},"@metamask/controller-utils>@metamask/ethjs-unit":{packages:{"@metamask/controller-utils>@metamask/ethjs-unit>@metamask/number-to-bn":!0,"ethereumjs-util>bn.js":!0}},"@metamask/controller-utils>@metamask/ethjs-unit>@metamask/number-to-bn":{packages:{"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>strip-hex-prefix":!0,"ethereumjs-util>bn.js":!0}},"@metamask/controller-utils>@spruceid/siwe-parser":{globals:{"console.error":!0,"console.log":!0},packages:{"@metamask/controller-utils>@spruceid/siwe-parser>apg-js":!0,"@noble/hashes":!0}},"@metamask/controller-utils>@spruceid/siwe-parser>apg-js":{packages:{buffer:!0}},"@metamask/core-backend":{globals:{URL:!0,fetch:!0},packages:{"@metamask/core-backend>@tanstack/query-core":!0}},"@metamask/core-backend>@tanstack/query-core":{globals:{AbortController:!0,addEventListener:!1,clearInterval:!0,clearTimeout:!0,"console.error":!0,document:!1,removeEventListener:!0,setInterval:!0,setTimeout:!0}},"@metamask/delegation-core":{packages:{"@metamask/abi-utils":!0,"@metamask/utils":!0,"@noble/hashes":!0}},"@metamask/design-system-react":{globals:{"console.warn":!0,"document.addEventListener":!0,"document.body":!0,"document.removeEventListener":!0},packages:{"@metamask/design-system-react>@radix-ui/react-slot":!0,"@metamask/design-system-react>blo":!0,"@metamask/design-system-react>tailwind-merge":!0,"@metamask/design-system-shared":!0,"@metamask/jazzicon":!0,react:!0,"react-dom":!0,"react-focus-lock":!0}},"@metamask/design-system-react>@radix-ui/react-slot":{packages:{"@metamask/design-system-react>@radix-ui/react-slot>@radix-ui/react-compose-refs":!0,react:!0}},"@metamask/design-system-react>@radix-ui/react-slot>@radix-ui/react-compose-refs":{packages:{react:!0}},"@metamask/design-system-react>blo":{globals:{btoa:!0}},"@metamask/design-system-shared":{packages:{"@metamask/utils":!0}},"@metamask/eth-hd-keyring":{globals:{"Buffer.concat":!0,"Buffer.from":!0,"Buffer.isBuffer":!0,TextEncoder:!0},packages:{"@ethereumjs/tx>@ethereumjs/util":!0,"@metamask/eth-hd-keyring>ethereum-cryptography":!0,"@metamask/eth-hd-keyring>ethereum-cryptography>@scure/bip32":!0,"@metamask/eth-sig-util":!0,"@metamask/keyring-api":!0,"@metamask/keyring-sdk":!0,"@metamask/scure-bip39":!0,"@metamask/snaps-sdk>@metamask/key-tree":!0,"@metamask/utils":!0,buffer:!0}},"@metamask/eth-hd-keyring>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0,module:!0},packages:{"@metamask/eth-hd-keyring>ethereum-cryptography>@noble/hashes":!0}},"@metamask/eth-hd-keyring>ethereum-cryptography>@noble/curves":{globals:{TextEncoder:!0},packages:{"@metamask/eth-hd-keyring>ethereum-cryptography>@noble/hashes":!0}},"@metamask/eth-hd-keyring>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0,crypto:!0}},"@metamask/eth-hd-keyring>ethereum-cryptography>@scure/bip32":{packages:{"@metamask/eth-hd-keyring>ethereum-cryptography>@noble/curves":!0,"@metamask/eth-hd-keyring>ethereum-cryptography>@noble/hashes":!0,"@metamask/eth-hd-keyring>ethereum-cryptography>@scure/bip32>@scure/base":!0}},"@metamask/eth-hd-keyring>ethereum-cryptography>@scure/bip32>@scure/base":{globals:{TextDecoder:!0,TextEncoder:!0}},"@metamask/eth-json-rpc-middleware":{globals:{setTimeout:!0},packages:{"@metamask/eth-json-rpc-middleware>safe-stable-stringify":!0,"@metamask/json-rpc-engine>klona":!0,"@metamask/rpc-errors":!0,"@metamask/utils":!0}},"@metamask/eth-json-rpc-provider":{packages:{"@metamask/json-rpc-engine":!0,nanoid:!0}},"@metamask/eth-ledger-bridge-keyring":{packages:{"@ethereumjs/tx":!0,"@ethereumjs/tx>@ethereumjs/util":!0,"@metamask/hw-wallet-sdk":!0,"@metamask/utils":!0}},"@metamask/eth-qr-keyring":{globals:{"Buffer.concat":!0,"Buffer.from":!0},packages:{"@ethereumjs/tx":!0,"@ethereumjs/tx>@ethereumjs/rlp":!0,"@ethereumjs/tx>@ethereumjs/util":!0,"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth":!0,"@metamask/eth-qr-keyring>hdkey":!0,"@metamask/eth-qr-keyring>uuid":!0,"@metamask/utils":!0,buffer:!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth":{globals:{"Buffer.from":!0},packages:{"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util":!0,"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@keystonehq/bc-ur-registry":!0,"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>uuid":!0,"@metamask/eth-qr-keyring>hdkey":!0,buffer:!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util":{globals:{"Buffer.alloc":!0,"Buffer.allocUnsafe":!0,"Buffer.byteLength":!0,"Buffer.concat":!0,"Buffer.from":!0,"Buffer.isBuffer":!0,"console.warn":!0},packages:{"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>@ethereumjs/rlp":!0,"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography":!0,buffer:!0,"eth-lattice-keyring>@ethereumjs/util>micro-ftch":!0,"webpack>events":!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>@ethereumjs/rlp":{globals:{TextEncoder:!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0},packages:{"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography>@noble/curves":!0,"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography>@noble/hashes":!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography>@noble/curves":{globals:{TextEncoder:!0},packages:{"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography>@noble/hashes":!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@ethereumjs/util>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0,crypto:!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>@keystonehq/bc-ur-registry":{globals:{Buffer:!0,define:!0},packages:{"@ngraveio/bc-ur":!0,buffer:!0,"ethereumjs-util>ethereum-cryptography>bs58check":!0,tslib:!0}},"@metamask/eth-qr-keyring>@keystonehq/bc-ur-registry-eth>uuid":{globals:{crypto:!0,msCrypto:!0}},"@metamask/eth-qr-keyring>hdkey":{packages:{"@ngraveio/bc-ur>assert":!0,"crypto-browserify":!0,"ethereumjs-util>create-hash>ripemd160":!0,"ethereumjs-util>ethereum-cryptography>bs58check":!0,"ethereumjs-util>ethereum-cryptography>secp256k1":!0,"mockttp>express>safe-buffer":!0}},"@metamask/eth-qr-keyring>uuid":{globals:{crypto:!0}},"@metamask/eth-sig-util":{globals:{"Buffer.byteLength":!0,"Buffer.concat":!0,"Buffer.from":!0},packages:{"@metamask/abi-utils":!0,"@metamask/eth-sig-util>@ethereumjs/rlp":!0,"@metamask/eth-sig-util>@ethereumjs/util":!0,"@metamask/eth-sig-util>@scure/base":!0,"@metamask/eth-sig-util>ethereum-cryptography":!0,"@metamask/utils":!0,buffer:!0,tweetnacl:!0}},"@metamask/eth-sig-util>@ethereumjs/rlp":{globals:{TextEncoder:!0}},"@metamask/eth-sig-util>@ethereumjs/util":{globals:{"Buffer.alloc":!0,"Buffer.allocUnsafe":!0,"Buffer.byteLength":!0,"Buffer.concat":!0,"Buffer.from":!0,"Buffer.isBuffer":!0,"console.warn":!0},packages:{"@metamask/eth-sig-util>@ethereumjs/rlp":!0,"@metamask/eth-sig-util>ethereum-cryptography":!0,buffer:!0,"eth-lattice-keyring>@ethereumjs/util>micro-ftch":!0,"webpack>events":!0}},"@metamask/eth-sig-util>@scure/base":{globals:{TextDecoder:!0,TextEncoder:!0}},"@metamask/eth-sig-util>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0},packages:{"@metamask/eth-sig-util>ethereum-cryptography>@noble/curves":!0,"@metamask/eth-sig-util>ethereum-cryptography>@noble/hashes":!0}},"@metamask/eth-sig-util>ethereum-cryptography>@noble/curves":{globals:{TextEncoder:!0},packages:{"@metamask/eth-sig-util>ethereum-cryptography>@noble/hashes":!0}},"@metamask/eth-sig-util>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0,crypto:!0}},"@metamask/eth-token-tracker":{globals:{"console.warn":!0},packages:{"@babel/runtime":!0,"@ethersproject/bignumber":!0,"@ethersproject/contracts":!0,"@ethersproject/providers":!0,"@metamask/eth-token-tracker>@metamask/eth-block-tracker":!0,"@metamask/eth-token-tracker>deep-equal":!0,"@metamask/safe-event-emitter":!0,"ethereumjs-util>bn.js":!0,"human-standard-token-abi":!0}},"@metamask/eth-token-tracker>@metamask/eth-block-tracker":{globals:{clearTimeout:!0,"console.error":!0,setTimeout:!0},packages:{"@metamask/ppom-validator>json-rpc-random-id":!0,"@metamask/safe-event-emitter":!0,"@metamask/utils":!0}},"@metamask/eth-token-tracker>deep-equal":{packages:{"@lavamoat/webpack>json-stable-stringify>isarray":!0,"@lavamoat/webpack>json-stable-stringify>object-keys":!0,"@metamask/eth-token-tracker>deep-equal>es-get-iterator":!0,"@metamask/eth-token-tracker>deep-equal>is-date-object":!0,"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive":!0,"@metamask/eth-token-tracker>deep-equal>which-collection":!0,"@ngraveio/bc-ur>assert>object-is":!0,"browserify>util>is-arguments":!0,"browserify>util>which-typed-array":!0,"gulp>vinyl-fs>object.assign":!0,"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>es-abstract>array-buffer-byte-length":!0,"string.prototype.matchall>es-abstract>is-array-buffer":!0,"string.prototype.matchall>es-abstract>is-regex":!0,"string.prototype.matchall>es-abstract>is-shared-array-buffer":!0,"string.prototype.matchall>get-intrinsic":!0,"string.prototype.matchall>regexp.prototype.flags":!0,"string.prototype.matchall>side-channel":!0}},"@metamask/eth-token-tracker>deep-equal>es-get-iterator":{globals:{process:!0},packages:{"@lavamoat/webpack>json-stable-stringify>isarray":!0,"@metamask/eth-token-tracker>deep-equal>es-get-iterator>is-map":!0,"browserify>util>is-arguments":!0,"eslint-plugin-react>array-includes>is-string":!0,process:!0,"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>es-abstract>is-set":!0,"string.prototype.matchall>es-abstract>stop-iteration-iterator":!0,"string.prototype.matchall>get-intrinsic":!0,"string.prototype.matchall>has-symbols":!0}},"@metamask/eth-token-tracker>deep-equal>is-date-object":{packages:{"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bound":!0}},"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive":{packages:{"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-bigint":!0,"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-boolean-object":!0,"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-number-object":!0,"eslint-plugin-react>array-includes>is-string":!0,"string.prototype.matchall>es-abstract>es-to-primitive>is-symbol":!0}},"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-bigint":{packages:{"string.prototype.matchall>es-abstract>unbox-primitive>has-bigints":!0}},"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-boolean-object":{packages:{"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bound":!0}},"@metamask/eth-token-tracker>deep-equal>which-boxed-primitive>is-number-object":{packages:{"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bound":!0}},"@metamask/eth-token-tracker>deep-equal>which-collection":{packages:{"@metamask/eth-token-tracker>deep-equal>es-get-iterator>is-map":!0,"@metamask/eth-token-tracker>deep-equal>which-collection>is-weakmap":!0,"@metamask/eth-token-tracker>deep-equal>which-collection>is-weakset":!0,"string.prototype.matchall>es-abstract>is-set":!0}},"@metamask/eth-token-tracker>deep-equal>which-collection>is-weakset":{packages:{"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>get-intrinsic":!0}},"@metamask/etherscan-link":{globals:{URL:!0}},"@metamask/gas-fee-controller":{globals:{clearInterval:!0,"console.error":!0,setInterval:!0},packages:{"@metamask/controller-utils":!0,"@metamask/controller-utils>@metamask/eth-query":!0,"@metamask/polling-controller":!0,"ethereumjs-util>bn.js":!0,uuid:!0}},"@metamask/jazzicon":{globals:{"document.createElement":!0,"document.createElementNS":!0},packages:{"@metamask/jazzicon>color":!0,"@metamask/jazzicon>mersenne-twister":!0}},"@metamask/jazzicon>color":{packages:{"@metamask/jazzicon>color>clone":!0,"@metamask/jazzicon>color>color-convert":!0,"@metamask/jazzicon>color>color-string":!0}},"@metamask/jazzicon>color>clone":{globals:{Buffer:!0},packages:{buffer:!0}},"@metamask/jazzicon>color>color-convert":{packages:{"@metamask/jazzicon>color>color-convert>color-name":!0}},"@metamask/jazzicon>color>color-string":{packages:{"jest-canvas-mock>moo-color>color-name":!0}},"@metamask/json-rpc-engine":{packages:{"@metamask/json-rpc-engine>klona":!0,"@metamask/messenger":!0,"@metamask/rpc-errors":!0,"@metamask/safe-event-emitter":!0,"@metamask/utils":!0,"deep-freeze-strict":!0}},"@metamask/json-rpc-middleware-stream":{globals:{"console.warn":!0,setTimeout:!0},packages:{"@metamask/json-rpc-middleware-stream>readable-stream":!0,"@metamask/safe-event-emitter":!0,"@metamask/utils":!0}},"@metamask/json-rpc-middleware-stream>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"@metamask/keyring-api":{packages:{"@metamask/keyring-utils":!0,"@metamask/superstruct":!0,"@metamask/utils":!0,"bitcoin-address-validation":!0}},"@metamask/keyring-controller":{globals:{"console.error":!0},packages:{"@ethereumjs/tx>@ethereumjs/util":!0,"@metamask/base-controller":!0,"@metamask/eth-hd-keyring":!0,"@metamask/eth-sig-util":!0,"@metamask/keyring-controller>@metamask/eth-simple-keyring":!0,"@metamask/keyring-controller>ethereumjs-wallet":!0,"@metamask/keyring-controller>ulid":!0,"@metamask/utils":!0,"async-mutex":!0,lodash:!0}},"@metamask/keyring-controller>@metamask/eth-simple-keyring":{globals:{"Buffer.concat":!0,"Buffer.from":!0},packages:{"@ethereumjs/tx>@ethereumjs/util":!0,"@metamask/eth-sig-util":!0,"@metamask/keyring-api":!0,"@metamask/keyring-controller>@metamask/eth-simple-keyring>ethereum-cryptography":!0,"@metamask/keyring-sdk":!0,"@metamask/utils":!0,buffer:!0,"crypto-browserify>randombytes":!0}},"@metamask/keyring-controller>@metamask/eth-simple-keyring>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0,module:!0},packages:{"@metamask/keyring-controller>@metamask/eth-simple-keyring>ethereum-cryptography>@noble/hashes":!0}},"@metamask/keyring-controller>@metamask/eth-simple-keyring>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0}},"@metamask/keyring-controller>ethereumjs-wallet":{globals:{"Buffer.alloc":!0,"Buffer.concat":!0,"Buffer.from":!0,"Buffer.isBuffer":!0},packages:{"@metamask/keyring-controller>ethereumjs-wallet>ethereum-cryptography":!0,"@metamask/keyring-controller>ethereumjs-wallet>ethereumjs-util":!0,"@metamask/keyring-controller>ethereumjs-wallet>utf8":!0,buffer:!0,"crypto-browserify":!0,"crypto-browserify>randombytes":!0,"eth-lattice-keyring>gridplus-sdk>aes-js":!0,"ethereumjs-util>ethereum-cryptography>bs58check":!0,"ethers>@ethersproject/json-wallets>scrypt-js":!0,uuid:!0}},"@metamask/keyring-controller>ethereumjs-wallet>ethereum-cryptography":{globals:{"Buffer.concat":!0,"Buffer.from":!0,"Buffer.isBuffer":!0},packages:{"@ngraveio/bc-ur>assert":!0,buffer:!0,"crypto-browserify>create-hmac":!0,"crypto-browserify>randombytes":!0,"ethereumjs-util>ethereum-cryptography>bs58check":!0,"ethereumjs-util>ethereum-cryptography>keccak":!0,"ethereumjs-util>ethereum-cryptography>secp256k1":!0,"ethers>@ethersproject/sha2>hash.js":!0,"mockttp>express>safe-buffer":!0}},"@metamask/keyring-controller>ethereumjs-wallet>ethereumjs-util":{globals:{Buffer:!0},packages:{"@metamask/keyring-controller>ethereumjs-wallet>ethereum-cryptography":!0,"@ngraveio/bc-ur>assert":!0,buffer:!0,"ethereumjs-util>bn.js":!0,"ethereumjs-util>create-hash":!0,"ethereumjs-util>rlp":!0}},"@metamask/keyring-controller>ulid":{globals:{"console.error":!0,crypto:!0,require:!0}},"@metamask/keyring-sdk":{packages:{"@ethereumjs/tx":!0,"@metamask/eth-sig-util":!0,"@metamask/keyring-api":!0,"@metamask/keyring-sdk>ethereum-cryptography":!0,"@metamask/keyring-sdk>uuid":!0,"@metamask/superstruct":!0,"@metamask/utils":!0,"async-mutex":!0}},"@metamask/keyring-sdk>ethereum-cryptography":{globals:{TextDecoder:!0,crypto:!0,module:!0},packages:{"@metamask/keyring-sdk>ethereum-cryptography>@noble/hashes":!0}},"@metamask/keyring-sdk>ethereum-cryptography>@noble/hashes":{globals:{TextEncoder:!0}},"@metamask/keyring-sdk>uuid":{globals:{crypto:!0}},"@metamask/keyring-snap-client":{packages:{"@metamask/keyring-api":!0,"@metamask/keyring-snap-client>uuid":!0,"@metamask/keyring-utils":!0,"@metamask/superstruct":!0}},"@metamask/keyring-snap-client>uuid":{globals:{crypto:!0}},"@metamask/keyring-utils":{globals:{URL:!0},packages:{"@metamask/superstruct":!0,"@metamask/utils":!0,"bitcoin-address-validation":!0}},"@metamask/logo":{globals:{addEventListener:!0,"document.body.appendChild":!0,"document.createElementNS":!0,innerHeight:!0,innerWidth:!0,requestAnimationFrame:!0},packages:{"@metamask/logo>gl-mat4":!0,"@metamask/logo>gl-vec3":!0}},"@metamask/messenger":{globals:{"console.error":!0}},"@metamask/multichain-network-controller":{packages:{"@metamask/keyring-api":!0,"@metamask/multichain-network-controller>@metamask/keyring-api":!0,"@metamask/network-controller":!0,"@metamask/utils":!0}},"@metamask/name-controller":{packages:{"@metamask/base-controller":!0,"@metamask/name-controller>@metamask/controller-utils":!0}},"@metamask/name-controller>@metamask/controller-utils":{globals:{"Buffer.from":!0,"console.error":!0,fetch:!0,setTimeout:!0},packages:{"@metamask/controller-utils>@metamask/ethjs-unit":!0,"@metamask/utils":!0,buffer:!0,"eslint>fast-deep-equal":!0,"eth-ens-namehash":!0,"ethereumjs-util>bn.js":!0,lodash:!0}},"@metamask/network-controller":{globals:{"Intl.NumberFormat":!0,URL:!0,"btoa.bind":!0,"fetch.bind":!0,setTimeout:!0},packages:{"@metamask/base-controller":!0,"@metamask/connectivity-controller":!0,"@metamask/controller-utils":!0,"@metamask/controller-utils>@metamask/eth-query":!0,"@metamask/eth-json-rpc-middleware":!0,"@metamask/eth-json-rpc-provider":!0,"@metamask/json-rpc-engine":!0,"@metamask/network-controller>@metamask/eth-block-tracker":!0,"@metamask/network-controller>@metamask/eth-json-rpc-infura":!0,"@metamask/network-controller>@metamask/swappable-obj-proxy":!0,"@metamask/rpc-errors":!0,"@metamask/utils":!0,"addons-linter>deepmerge":!0,cockatiel:!0,"eslint>fast-deep-equal":!0,immer:!0,lodash:!0,reselect:!0,"uri-js":!0,uuid:!0}},"@metamask/network-controller>@metamask/eth-block-tracker":{globals:{clearTimeout:!0,"console.error":!0,setTimeout:!0},packages:{"@metamask/ppom-validator>json-rpc-random-id":!0,"@metamask/safe-event-emitter":!0,"@metamask/utils":!0}},"@metamask/network-controller>@metamask/eth-json-rpc-infura":{globals:{fetch:!0,setTimeout:!0},packages:{"@metamask/json-rpc-engine":!0,"@metamask/network-controller>@metamask/eth-json-rpc-infura>@metamask/eth-json-rpc-provider":!0,"@metamask/rpc-errors":!0,"@metamask/utils":!0}},"@metamask/network-controller>@metamask/eth-json-rpc-infura>@metamask/eth-json-rpc-provider":{packages:{"@metamask/json-rpc-engine":!0,"@metamask/rpc-errors":!0,"@metamask/safe-event-emitter":!0,uuid:!0}},"@metamask/notification-services-controller":{globals:{"Intl.NumberFormat":!0,"console.error":!0,fetch:!0},packages:{"@metamask/authenticated-user-storage":!0,"@metamask/base-controller":!0,"@metamask/controller-utils":!0,"@metamask/notification-services-controller>@contentful/rich-text-html-renderer":!0,"@metamask/notification-services-controller>bignumber.js":!0,"@metamask/utils":!0,lodash:!0,loglevel:!0,semver:!0,uuid:!0}},"@metamask/notification-services-controller>@contentful/rich-text-html-renderer":{globals:{SuppressedError:!0}},"@metamask/notification-services-controller>bignumber.js":{globals:{crypto:!0}},"@metamask/object-multiplex":{globals:{"console.warn":!0},packages:{"@metamask/object-multiplex>once":!0,"@metamask/object-multiplex>readable-stream":!0}},"@metamask/object-multiplex>once":{packages:{"@metamask/object-multiplex>once>wrappy":!0}},"@metamask/object-multiplex>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"@metamask/permission-controller":{globals:{"console.error":!0},packages:{"@metamask/base-controller":!0,"@metamask/controller-utils":!0,"@metamask/rpc-errors":!0,"@metamask/utils":!0,"deep-freeze-strict":!0,immer:!0,nanoid:!0}},"@metamask/perps-controller":{packages:{"@metamask/utils":!0}},"@metamask/polling-controller":{globals:{clearTimeout:!0,"console.error":!0,setTimeout:!0},packages:{"@metamask/base-controller":!0,"fast-json-stable-stringify":!0,uuid:!0}},"@metamask/post-message-stream":{globals:{"MessageEvent.prototype":!0,WorkerGlobalScope:!0,addEventListener:!0,browser:!0,chrome:!0,"location.origin":!0,postMessage:!0,removeEventListener:!0},packages:{"@metamask/post-message-stream>readable-stream":!0,"@metamask/utils":!0}},"@metamask/post-message-stream>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"@metamask/ppom-validator>crypto-js":{globals:{crypto:!0,define:!0,msCrypto:!0}},"@metamask/providers":{globals:{console:!0},packages:{"@metamask/json-rpc-engine":!0,"@metamask/json-rpc-middleware-stream":!0,"@metamask/providers>is-stream":!0,"@metamask/providers>readable-stream":!0,"@metamask/rpc-errors":!0,"@metamask/safe-event-emitter":!0,"eslint>fast-deep-equal":!0}},"@metamask/providers>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"@metamask/react-data-query":{packages:{"@metamask/utils":!0,"@tanstack/react-query>@tanstack/query-core":!0}},"@metamask/rpc-errors":{packages:{"@metamask/rpc-errors>fast-safe-stringify":!0,"@metamask/utils":!0}},"@metamask/safe-event-emitter":{globals:{setTimeout:!0},packages:{"webpack>events":!0}},"@metamask/scure-bip39":{globals:{TextEncoder:!0},packages:{"@metamask/scure-bip39>@noble/hashes":!0,"@metamask/scure-bip39>@scure/base":!0}},"@metamask/scure-bip39>@noble/hashes":{globals:{TextEncoder:!0,crypto:!0}},"@metamask/scure-bip39>@scure/base":{globals:{TextDecoder:!0,TextEncoder:!0}},"@metamask/smart-transactions-controller":{packages:{"@metamask/superstruct":!0,"@metamask/utils":!0,reselect:!0}},"@metamask/snaps-execution-environments":{globals:{"document.getElementById":!0},packages:{"@metamask/post-message-stream":!0,"@metamask/snaps-utils":!0,"@metamask/utils":!0}},"@metamask/snaps-rpc-methods":{packages:{"@metamask/permission-controller":!0,"@metamask/rpc-errors":!0,"@metamask/snaps-sdk":!0,"@metamask/snaps-utils":!0,"@metamask/superstruct":!0,"@metamask/utils":!0}},"@metamask/snaps-sdk":{globals:{URL:!0},packages:{"@metamask/superstruct":!0,"@metamask/utils":!0,luxon:!0}},"@metamask/snaps-sdk>@metamask/key-tree":{globals:{"crypto.subtle":!0,ed25519:!0,ed25519Bip32:!0,secp256k1:!0},packages:{"@metamask/scure-bip39":!0,"@metamask/utils":!0,"@noble/curves":!0,"@noble/hashes":!0,"@scure/base":!0}},"@metamask/snaps-utils":{globals:{File:!0,FileReader:!0,TextDecoder:!0,URL:!0,"console.error":!0,"console.log":!0,"console.warn":!0,"document.body.appendChild":!0,"document.createElement":!0,fetch:!0,navigator:!0},packages:{"@metamask/permission-controller":!0,"@metamask/snaps-sdk":!0,"@metamask/snaps-sdk>@metamask/key-tree":!0,"@metamask/snaps-utils>@metamask/slip44":!0,"@metamask/snaps-utils>marked":!0,"@metamask/snaps-utils>rfdc":!0,"@metamask/snaps-utils>validate-npm-package-name":!0,"@metamask/superstruct":!0,"@metamask/utils":!0,"@scure/base":!0,chalk:!0,"cron-parser":!0,"fast-json-stable-stringify":!0,luxon:!0}},"@metamask/snaps-utils>marked":{globals:{"console.error":!0,"console.warn":!0}},"@metamask/snaps-utils>rfdc":{globals:{Buffer:!0},packages:{buffer:!0}},"@metamask/snaps-utils>validate-npm-package-name":{packages:{"@metamask/snaps-utils>validate-npm-package-name>builtins":!0}},"@metamask/snaps-utils>validate-npm-package-name>builtins":{globals:{"process.version":!0},packages:{process:!0,semver:!0}},"@metamask/transaction-controller":{globals:{"Buffer.from":!0,clearInterval:!0,clearTimeout:!0,"console.error":!0,fetch:!0,setInterval:!0,setTimeout:!0},packages:{"@ethereumjs/tx":!0,"@ethereumjs/tx>@ethereumjs/common":!0,"@ethersproject/abi":!0,"@ethersproject/contracts":!0,"@ethersproject/providers":!0,"@metamask/base-controller":!0,"@metamask/controller-utils":!0,"@metamask/gas-fee-controller":!0,"@metamask/metamask-eth-abis":!0,"@metamask/network-controller":!0,"@metamask/rpc-errors":!0,"@metamask/transaction-controller>@metamask/nonce-tracker":!0,"@metamask/transaction-controller>bignumber.js":!0,"@metamask/utils":!0,"async-mutex":!0,buffer:!0,"eth-method-registry":!0,"ethereumjs-util>bn.js":!0,"ethers>@ethersproject/wallet":!0,lodash:!0,uuid:!0,"webpack>events":!0}},"@metamask/transaction-controller>@metamask/nonce-tracker":{packages:{"@ethersproject/providers":!0,"@metamask/transaction-controller>@metamask/nonce-tracker>async-mutex":!0,"@ngraveio/bc-ur>assert":!0}},"@metamask/transaction-controller>@metamask/nonce-tracker>async-mutex":{globals:{clearTimeout:!0,setTimeout:!0},packages:{tslib:!0}},"@metamask/transaction-controller>bignumber.js":{globals:{crypto:!0}},"@metamask/transaction-pay-controller":{packages:{"@metamask/transaction-controller":!0}},"@metamask/utils":{globals:{Buffer:!0,TextDecoder:!0,TextEncoder:!0,crypto:!0},packages:{"@metamask/superstruct":!0,"@metamask/utils>pony-cause":!0,"@noble/hashes":!0,"@scure/base":!0,buffer:!0,lodash:!0,"nock>debug":!0,semver:!0}},"@mui/material":{globals:{CSS:!0,DocumentFragment:!0,IntersectionObserver:!0,MutationObserver:!0,ResizeObserver:!0,addEventListener:!0,cancelAnimationFrame:!0,clearInterval:!0,clearTimeout:!0,"console.error":!0,"console.warn":!0,"document.activeElement":!0,"document.body":!0,getSelection:!0,navigator:!0,"performance.now":!0,removeEventListener:!0,requestAnimationFrame:!0,setInterval:!0,setTimeout:!0},packages:{"@babel/runtime":!0,"@emotion/react":!0,"@mui/material>react-is":!0,"@mui/system":!0,"@mui/system>@mui/utils":!0,clsx:!0,"prop-types":!0,react:!0,"react-dom":!0,"react-transition-group":!0}},"@mui/system":{globals:{"console.error":!0,"console.warn":!0,"document.createElement":!0,"document.querySelector":!0,matchMedia:!0},packages:{"@babel/runtime":!0,"@emotion/react":!0,"@mui/system>@mui/private-theming":!0,"@mui/system>@mui/styled-engine":!0,"@mui/system>@mui/utils":!0,"prop-types":!0,react:!0}},"@mui/system>@mui/private-theming":{globals:{"console.error":!0},packages:{"@babel/runtime":!0,"@mui/system>@mui/utils":!0,"prop-types":!0,react:!0}},"@mui/system>@mui/styled-engine":{globals:{"console.error":!0,document:!0},packages:{"@emotion/react":!0,"@emotion/react>@emotion/cache":!0,"@emotion/react>@emotion/serialize":!0,"@emotion/styled":!0,"prop-types":!0,react:!0}},"@mui/system>@mui/utils":{globals:{clearTimeout:!0,"console.error":!0,document:!0,innerWidth:!0,setTimeout:!0},packages:{"@babel/runtime":!0,"@mui/system>@mui/utils>react-is":!0,clsx:!0,react:!0}},"@mui/x-date-pickers":{globals:{Intl:!0,Range:!0,addEventListener:!0,clearTimeout:!0,"console.error":!0,"console.warn":!0,document:!0,innerHeight:!0,navigator:!0,orientation:!0,removeEventListener:!0,screen:!0,setTimeout:!0},packages:{"@babel/runtime":!0,"@mui/material":!0,"@mui/system":!0,"@mui/x-date-pickers>@mui/utils":!0,"@mui/x-date-pickers>@mui/x-internals":!0,clsx:!0,luxon:!0,"prop-types":!0,react:!0,"react-transition-group":!0}},"@mui/x-date-pickers>@mui/utils":{globals:{URL:!0,"console.error":!0},packages:{clsx:!0,"prop-types":!0,react:!0}},"@ngraveio/bc-ur":{globals:{"Buffer.alloc":!0,"Buffer.allocUnsafe":!0,"Buffer.concat":!0,"Buffer.from":!0,"Buffer.isBuffer":!0},packages:{"@ngraveio/bc-ur>@keystonehq/alias-sampling":!0,"@ngraveio/bc-ur>assert":!0,"@ngraveio/bc-ur>bignumber.js":!0,"@ngraveio/bc-ur>cbor-sync":!0,"@ngraveio/bc-ur>crc":!0,"@ngraveio/bc-ur>jsbi":!0,"@ngraveio/bc-ur>sha.js":!0,buffer:!0}},"@ngraveio/bc-ur>assert":{globals:{console:!0,"process.emitWarning":!0,"process.stderr":!0},packages:{"@ngraveio/bc-ur>assert>is-nan":!0,"@ngraveio/bc-ur>assert>object-is":!0,"browserify>util":!0,"gulp>vinyl-fs>object.assign":!0,process:!0,"string.prototype.matchall>call-bind":!0}},"@ngraveio/bc-ur>assert>is-nan":{packages:{"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>define-properties":!0}},"@ngraveio/bc-ur>assert>object-is":{packages:{"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>define-properties":!0}},"@ngraveio/bc-ur>bignumber.js":{globals:{crypto:!0,define:!0}},"@ngraveio/bc-ur>cbor-sync":{globals:{Buffer:!0,define:!0},packages:{buffer:!0}},"@ngraveio/bc-ur>crc":{packages:{"@ngraveio/bc-ur>crc>buffer":!0}},"@ngraveio/bc-ur>crc>buffer":{globals:{console:!0},packages:{"base64-js":!0,"buffer>ieee754":!0}},"@ngraveio/bc-ur>jsbi":{globals:{define:!0}},"@ngraveio/bc-ur>sha.js":{packages:{"@ngraveio/bc-ur>sha.js>to-buffer":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0}},"@ngraveio/bc-ur>sha.js>to-buffer":{packages:{"@lavamoat/webpack>json-stable-stringify>isarray":!0,"mockttp>express>safe-buffer":!0,"string.prototype.matchall>es-abstract>typed-array-buffer":!0}},"@noble/curves":{packages:{"@noble/hashes":!0}},"@noble/hashes":{globals:{TextDecoder:!0,TextEncoder:!0,crypto:!0}},"@open-rpc/test-coverage>isomorphic-fetch>whatwg-fetch":{globals:{DOMException:!0,fetch:!0}},"@popperjs/core":{globals:{Element:!0,HTMLElement:!0,ShadowRoot:!0,devicePixelRatio:!0,document:!0,"navigator.userAgent":!0,"navigator.userAgentData":!0}},"@reduxjs/toolkit":{globals:{AbortController:!0,__REDUX_DEVTOOLS_EXTENSION_COMPOSE__:!0,__REDUX_DEVTOOLS_EXTENSION__:!0,console:!0,process:!0,queueMicrotask:!0,requestAnimationFrame:!0,setTimeout:!0},packages:{"@reduxjs/toolkit>reselect":!0,immer:!0,process:!0,redux:!0,"redux-thunk":!0}},"@rive-app/react-canvas":{globals:{IntersectionObserver:!0,ResizeObserver:!0,addEventListener:!0,clearTimeout:!0,"console.error":!0,devicePixelRatio:!0,"document.documentElement.clientHeight":!0,"document.documentElement.clientWidth":!0,innerHeight:!0,innerWidth:!0,matchMedia:!0,removeEventListener:!0,setTimeout:!0},packages:{"@rive-app/react-canvas>@rive-app/canvas":!0,react:!0}},"@rive-app/react-canvas>@rive-app/canvas":{globals:{AudioContext:!1,Blob:!0,DOMMatrix:!1,FinalizationRegistry:!1,HTMLCanvasElement:!0,Image:!0,Iterator:!1,MouseEvent:!1,Path2D:!0,Request:!0,ResizeObserver:!1,TextDecoder:!0,"URL.createObjectURL":!0,"URL.revokeObjectURL":!0,WebAssembly:!0,XMLHttpRequest:!1,cancelAnimationFrame:!0,clearInterval:!0,clearTimeout:!0,console:!0,crypto:!1,define:!1,devicePixelRatio:!0,document:!1,"document.createElement":!0,fetch:!1,h:!1,importScripts:!1,location:!1,navigator:!1,"navigator.userAgent":!0,"performance.now":!0,prompt:!1,readline:!1,requestAnimationFrame:!0,setTimeout:!0,webkitAudioContext:!1}},"@scure/base":{globals:{TextDecoder:!0,TextEncoder:!0}},"@segment/analytics-node":{globals:{AbortController:!0,EdgeRuntime:!1,URL:!0,WebSocketPair:!1,WorkerGlobalScope:!1,clearTimeout:!0,"console.warn":!0,fetch:!0,importScripts:!1,process:!0,setTimeout:!0},packages:{"@segment/analytics-node>@lukeed/uuid":!0,"@segment/analytics-node>@segment/analytics-core":!0,"@segment/analytics-node>@segment/analytics-generic-utils":!0,"@segment/analytics-node>jose":!0,process:!0}},"@segment/analytics-node>@segment/analytics-core":{globals:{clearTimeout:!0,console:!0,setTimeout:!0},packages:{"@segment/analytics-node>@lukeed/uuid":!0,"@segment/analytics-node>@segment/analytics-core>dset":!0,"@segment/analytics-node>@segment/analytics-generic-utils":!0,tslib:!0}},"@segment/analytics-node>@segment/analytics-generic-utils":{globals:{"console.warn":!0}},"@segment/analytics-node>jose":{globals:{CryptoKey:!0,TextDecoder:!0,TextEncoder:!0,atob:!0,btoa:!0,crypto:!0}},"@sentry/browser":{globals:{"PerformanceObserver.supportedEntryTypes":!0,Request:!0,URL:!0,"XMLHttpRequest.prototype":!0,__SENTRY_DEBUG__:!0,__SENTRY_RELEASE__:!0,addEventListener:!0,"console.error":!0,"indexedDB.open":!0,"performance.timeOrigin":!0,setTimeout:!0},packages:{"@sentry/browser>@sentry-internal/browser-utils":!0,"@sentry/browser>@sentry-internal/feedback":!0,"@sentry/browser>@sentry-internal/replay":!0,"@sentry/browser>@sentry-internal/replay-canvas":!0,"@sentry/browser>@sentry/core":!0,"@sentry/utils":!0}},"@sentry/browser>@sentry-internal/browser-utils":{globals:{"PerformanceEventTiming.prototype":!0,PerformanceObserver:!0,"XMLHttpRequest.prototype":!0,__SENTRY_DEBUG__:!0,addEventListener:!0,clearTimeout:!0,performance:!0,removeEventListener:!0,setTimeout:!0},packages:{"@sentry/browser>@sentry/core":!0,"@sentry/utils":!0}},"@sentry/browser>@sentry-internal/feedback":{globals:{FormData:!0,HTMLFormElement:!0,__SENTRY_DEBUG__:!0,cancelAnimationFrame:!0,clearTimeout:!0,"document.createElement":!0,"document.createElementNS":!0,"document.createTextNode":!0,isSecureContext:!0,requestAnimationFrame:!0,setTimeout:!0},packages:{"@sentry/browser>@sentry/core":!0,"@sentry/utils":!0}},"@sentry/browser>@sentry-internal/replay":{globals:{Blob:!0,CSSConditionRule:!0,CSSGroupingRule:!0,CSSMediaRule:!0,CSSRule:!0,CSSSupportsRule:!0,Document:!0,DragEvent:!0,Element:!0,FormData:!0,HTMLElement:!0,HTMLFormElement:!0,Headers:!0,MouseEvent:!0,MutationObserver:!0,"Node.DOCUMENT_FRAGMENT_NODE":!0,"Node.prototype.contains":!0,PointerEvent:!0,TextEncoder:!0,URL:!0,URLSearchParams:!0,Worker:!0,__RRWEB_EXCLUDE_IFRAME__:!0,__RRWEB_EXCLUDE_SHADOW_DOM__:!0,__SENTRY_DEBUG__:!0,__SENTRY_EXCLUDE_REPLAY_WORKER__:!0,__rrMutationObserver:!0,addEventListener:!0,clearTimeout:!0,"console.debug":!0,"console.error":!0,"console.warn":!0,"customElements.get":!0,document:!0,innerHeight:!0,innerWidth:!0,"location.href":!0,"location.origin":!0,parent:!0,setTimeout:!0},packages:{"@sentry/browser>@sentry-internal/browser-utils":!0,"@sentry/browser>@sentry/core":!0,"@sentry/utils":!0}},"@sentry/browser>@sentry-internal/replay-canvas":{globals:{Blob:!0,HTMLCanvasElement:!0,HTMLImageElement:!0,ImageData:!0,"URL.createObjectURL":!0,WeakRef:!0,Worker:!0,cancelAnimationFrame:!0,"console.error":!0,createImageBitmap:!0,document:!0},packages:{"@sentry/browser>@sentry/core":!0,"@sentry/utils":!0}},"@sentry/browser>@sentry/core":{globals:{Headers:!0,Request:!0,URL:!0,__SENTRY_DEBUG__:!0,__SENTRY_TRACING__:!0,clearInterval:!0,clearTimeout:!0,"console.log":!0,"console.warn":!0,setInterval:!0,setTimeout:!0},packages:{"@sentry/utils":!0}},"@sentry/utils":{globals:{CustomEvent:!0,DOMError:!0,DOMException:!0,EdgeRuntime:!0,Element:!0,ErrorEvent:!0,Event:!0,HTMLElement:!0,Headers:!0,PerformanceObserver:!0,Request:!0,Response:!0,TextDecoder:!0,TextEncoder:!0,__SENTRY_BROWSER_BUNDLE__:!0,__SENTRY_DEBUG__:!0,addEventListener:!0,"chrome.app":!0,"chrome.runtime":!0,clearTimeout:!0,"console.error":!0,crypto:!0,devicePixelRatio:!0,document:!0,location:!1,"location.href":!0,module:!0,"navigator.language":!0,"navigator.userAgent":!0,"navigator.userAgentData":!0,onunhandledrejection:!0,"performance.now":!0,"performance.timeOrigin":!0,process:!0,setTimeout:!0,top:!0},packages:{process:!0}},"@simplewebauthn/browser":{globals:{AbortController:!0,AbortSignal:!0,PublicKeyCredential:!0,atob:!0,btoa:!0,"console.warn":!0,"document.querySelectorAll":!0,"location.hostname":!0,"navigator.credentials.create":!0,"navigator.credentials.get":!0}},"@solana/addresses":{globals:{"Intl.Collator":!0,TextEncoder:!0,"crypto.subtle.digest":!0,"crypto.subtle.exportKey":!0},packages:{"@solana/addresses>@solana/assertions":!0,"@solana/addresses>@solana/codecs-core":!0,"@solana/addresses>@solana/codecs-strings":!0,"@solana/addresses>@solana/errors":!0}},"@solana/addresses>@solana/codecs-core":{packages:{"@solana/addresses>@solana/errors":!0}},"@solana/addresses>@solana/codecs-strings":{globals:{TextDecoder:!0,TextEncoder:!0,atob:!0,btoa:!0},packages:{"@solana/addresses>@solana/codecs-core":!0,"@solana/addresses>@solana/errors":!0}},"@solana/addresses>@solana/errors":{globals:{btoa:!0}},"@storybook/addon-docs>remark-external-links>mdast-util-definitions":{packages:{"react-markdown>unist-util-visit":!0}},"@storybook/react>util-deprecate":{globals:{"console.trace":!0,"console.warn":!0,localStorage:!0}},"@tanstack/react-query":{globals:{ReactQueryClientContext:"write"},packages:{"@tanstack/react-query>@tanstack/query-core":!0,"@tanstack/react-query>use-sync-external-store":!0,react:!0}},"@tanstack/react-query>@tanstack/query-core":{globals:{AbortController:!0,addEventListener:!1,clearInterval:!0,clearTimeout:!0,console:!0,document:!1,navigator:!0,removeEventListener:!0,setInterval:!0,setTimeout:!0}},"@tanstack/react-query>use-sync-external-store":{globals:{__REACT_DEVTOOLS_GLOBAL_HOOK__:!1,document:!1,"document.createElement":!0},packages:{react:!0}},"@tanstack/react-virtual":{globals:{document:!0,scrollY:!0},packages:{"@tanstack/react-virtual>@tanstack/virtual-core":!0,react:!0,"react-dom":!0}},"@tanstack/react-virtual>@tanstack/virtual-core":{globals:{"console.info":!0,"console.warn":!0,requestAnimationFrame:!0}},"@toruslabs/eccrypto>elliptic":{packages:{"@toruslabs/eccrypto>elliptic>brorand":!0,"@toruslabs/eccrypto>elliptic>hmac-drbg":!0,"@toruslabs/eccrypto>elliptic>minimalistic-assert":!0,"@toruslabs/eccrypto>elliptic>minimalistic-crypto-utils":!0,"ethereumjs-util>bn.js":!0,"ethers>@ethersproject/sha2>hash.js":!0,"pumpify>inherits":!0}},"@toruslabs/eccrypto>elliptic>brorand":{globals:{crypto:!0,msCrypto:!0}},"@toruslabs/eccrypto>elliptic>hmac-drbg":{packages:{"@toruslabs/eccrypto>elliptic>minimalistic-assert":!0,"@toruslabs/eccrypto>elliptic>minimalistic-crypto-utils":!0,"ethers>@ethersproject/sha2>hash.js":!0}},"@trezor/connect-web":{globals:{URLSearchParams:!0,__TREZOR_CONNECT_SRC:!0,addEventListener:!0,btoa:!0,chrome:!0,clearInterval:!0,clearTimeout:!0,"console.warn":!0,"document.body":!0,"document.createElement":!0,"document.createTextNode":!0,"document.getElementById":!0,"document.querySelectorAll":!0,"location.origin":!0,navigator:!0,open:!0,origin:!0,removeEventListener:!0,setInterval:!0,setTimeout:!0},packages:{"@trezor/connect-web>@trezor/connect":!0,"@trezor/connect-web>@trezor/connect-common":!0,"@trezor/connect-web>@trezor/connect>@trezor/blockchain-link>@trezor/websocket-client":!0,"@trezor/connect-web>@trezor/utils":!0,tslib:!0,"webpack>events":!0}},"@trezor/connect-web>@trezor/connect":{packages:{"@trezor/connect-web>@trezor/connect>@trezor/device-utils":!0,"@trezor/connect-web>@trezor/connect>@trezor/protobuf":!0,"@trezor/connect-web>@trezor/connect>@trezor/schema-utils":!0,"@trezor/connect-web>@trezor/connect>@trezor/transport":!0,"@trezor/connect-web>@trezor/utils":!0,tslib:!0}},"@trezor/connect-web>@trezor/connect-common":{globals:{"console.warn":!0,"localStorage.getItem":!0,"localStorage.setItem":!0,navigator:!0,setTimeout:!0,window:!0},packages:{"@trezor/connect-web>@trezor/connect-common>@trezor/env-utils":!0,"@trezor/connect-web>@trezor/utils":!0,tslib:!0}},"@trezor/connect-web>@trezor/connect-common>@trezor/env-utils":{globals:{innerHeight:!0,innerWidth:!0,"location.hostname":!0,"location.origin":!0,"navigator.languages":!0,"navigator.platform":!0,"navigator.userAgent":!0,process:!0,"screen.height":!0,"screen.width":!0},packages:{"@trezor/connect-web>@trezor/connect-common>@trezor/env-utils>ua-parser-js":!0,process:!0}},"@trezor/connect-web>@trezor/connect-common>@trezor/env-utils>ua-parser-js":{globals:{define:!0,"navigator.userAgentData":!0}},"@trezor/connect-web>@trezor/connect>@trezor/blockchain-link>@trezor/websocket-client":{globals:{WebSocket:!0,clearTimeout:!0,setTimeout:!0},packages:{"@trezor/connect-web>@trezor/utils":!0,tslib:!0,"webpack>events":!0}},"@trezor/connect-web>@trezor/connect>@trezor/device-utils":{packages:{tslib:!0}},"@trezor/connect-web>@trezor/connect>@trezor/protobuf":{globals:{"Buffer.from":!0},packages:{"@google/genai>protobufjs":!0,"@trezor/connect-web>@trezor/connect>@trezor/protobuf>long":!0,"@trezor/connect-web>@trezor/connect>@trezor/schema-utils":!0,buffer:!0,tslib:!0}},"@trezor/connect-web>@trezor/connect>@trezor/protobuf>long":{globals:{"WebAssembly.Instance":!0,"WebAssembly.Module":!0,define:!0}},"@trezor/connect-web>@trezor/connect>@trezor/schema-utils":{globals:{Buffer:!0,"console.warn":!0},packages:{"@trezor/connect-web>@trezor/connect>@trezor/schema-utils>@sinclair/typebox":!0,buffer:!0,"ts-mixer":!0}},"@trezor/connect-web>@trezor/utils":{globals:{AbortController:!0,Blob:!0,"Buffer.alloc":!0,"Buffer.allocUnsafe":!0,"Intl.NumberFormat":!0,TextEncoder:!0,clearInterval:!0,clearTimeout:!0,"console.error":!0,"console.info":!0,"console.log":!0,"console.warn":!0,"crypto.getRandomValues":!0,setInterval:!0,setTimeout:!0},packages:{"@trezor/connect-web>@trezor/utils>bignumber.js":!0,buffer:!0,tslib:!0,"webpack>events":!0}},"@trezor/connect-web>@trezor/utils>bignumber.js":{globals:{crypto:!0,define:!0}},"@zxing/browser":{globals:{HTMLElement:!0,HTMLImageElement:!0,HTMLVideoElement:!0,clearTimeout:!0,"console.error":!0,"console.warn":!0,document:!0,navigator:!0,setTimeout:!0},packages:{"@zxing/library":!0}},"@zxing/library":{globals:{HTMLImageElement:!0,HTMLVideoElement:!0,TextDecoder:!0,TextEncoder:!0,"URL.createObjectURL":!0,btoa:!0,"console.log":!0,"console.warn":!0,document:!0,navigator:!0,setTimeout:!0},packages:{"@zxing/library>ts-custom-error":!0}},"async-mutex":{globals:{clearTimeout:!0,setTimeout:!0}},"bignumber.js":{globals:{crypto:!0,define:!0}},bowser:{globals:{define:!0}},"browserify>string_decoder":{packages:{"mockttp>express>safe-buffer":!0}},"browserify>url":{packages:{"browserify>url>punycode":!0,"mockttp>express>qs":!0}},"browserify>url>punycode":{globals:{define:!0}},"browserify>util":{globals:{SharedArrayBuffer:!0,"console.error":!0,"console.log":!0,"console.trace":!0,process:!0},packages:{"browserify>util>is-arguments":!0,"browserify>util>is-generator-function":!0,"browserify>util>is-typed-array":!0,"browserify>util>which-typed-array":!0,process:!0,"pumpify>inherits":!0}},"browserify>util>is-arguments":{packages:{"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bind":!0}},"browserify>util>is-generator-function":{packages:{"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-abstract>get-proto":!0,"string.prototype.matchall>es-abstract>safe-regex-test":!0,"string.prototype.matchall>get-intrinsic>generator-function":!0}},"browserify>util>is-typed-array":{packages:{"browserify>util>which-typed-array":!0}},"browserify>util>which-typed-array":{packages:{"browserify>util>which-typed-array>for-each":!0,"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-abstract>available-typed-arrays":!0,"string.prototype.matchall>es-abstract>get-proto":!0,"string.prototype.matchall>gopd":!0}},"browserify>util>which-typed-array>for-each":{packages:{"string.prototype.matchall>es-abstract>is-callable":!0}},buffer:{globals:{SharedArrayBuffer:!0,console:!0},packages:{"base64-js":!0,"buffer>ieee754":!0}},chalk:{packages:{"chalk>ansi-styles":!0,"chalk>supports-color":!0}},"chalk>ansi-styles":{packages:{"chalk>ansi-styles>color-convert":!0}},"chalk>ansi-styles>color-convert":{packages:{"jest-canvas-mock>moo-color>color-name":!0}},"chart.js":{globals:{"Intl.NumberFormat":!0,MutationObserver:!0,OffscreenCanvas:!0,Path2D:!0,ResizeObserver:!0,addEventListener:!0,clearTimeout:!0,"console.error":!0,"console.warn":!0,devicePixelRatio:!0,document:!0,removeEventListener:!0,requestAnimationFrame:!0,setTimeout:!0},packages:{"chart.js>@kurkle/color":!0}},cockatiel:{globals:{AbortController:!0,AbortSignal:!0,WeakRef:!0,performance:!0,"process.hrtime.bigint":!0,setTimeout:!0},packages:{process:!0}},"copy-to-clipboard":{globals:{clipboardData:!0,"console.error":!0,"console.warn":!0,"document.body.appendChild":!0,"document.body.removeChild":!0,"document.createElement":!0,"document.createRange":!0,"document.execCommand":!0,"document.getSelection":!0,"navigator.userAgent":!0,prompt:!0},packages:{"copy-to-clipboard>toggle-selection":!0}},"copy-to-clipboard>toggle-selection":{globals:{"document.activeElement":!0,"document.getSelection":!0}},"core-js-pure":{globals:{"Bun.version":!0,"Deno.version":!0,document:!0,setTimeout:!0}},"cron-parser":{packages:{luxon:!0}},"crypto-browserify":{packages:{"crypto-browserify>browserify-cipher":!0,"crypto-browserify>browserify-sign":!0,"crypto-browserify>create-ecdh":!0,"crypto-browserify>create-hmac":!0,"crypto-browserify>diffie-hellman":!0,"crypto-browserify>pbkdf2":!0,"crypto-browserify>public-encrypt":!0,"crypto-browserify>randombytes":!0,"crypto-browserify>randomfill":!0,"ethereumjs-util>create-hash":!0}},"crypto-browserify>browserify-cipher":{packages:{"crypto-browserify>browserify-cipher>browserify-des":!0,"crypto-browserify>browserify-cipher>evp_bytestokey":!0,"ethereumjs-util>ethereum-cryptography>browserify-aes":!0}},"crypto-browserify>browserify-cipher>browserify-des":{globals:{Buffer:!0},packages:{buffer:!0,"crypto-browserify>browserify-cipher>browserify-des>des.js":!0,"ethereumjs-util>create-hash>cipher-base":!0,"pumpify>inherits":!0}},"crypto-browserify>browserify-cipher>browserify-des>des.js":{packages:{"@toruslabs/eccrypto>elliptic>minimalistic-assert":!0,"pumpify>inherits":!0}},"crypto-browserify>browserify-cipher>evp_bytestokey":{packages:{"ethereumjs-util>create-hash>md5.js":!0,"mockttp>express>safe-buffer":!0}},"crypto-browserify>browserify-sign":{packages:{"@toruslabs/eccrypto>elliptic":!0,"crypto-browserify>browserify-sign>readable-stream":!0,"crypto-browserify>create-hmac":!0,"crypto-browserify>public-encrypt>browserify-rsa":!0,"crypto-browserify>public-encrypt>parse-asn1":!0,"ethereumjs-util>bn.js":!0,"ethereumjs-util>create-hash":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0}},"crypto-browserify>browserify-sign>readable-stream":{globals:{"process.browser":!0,"process.stderr":!0,"process.stdout":!0,"process.version.slice":!0,setImmediate:!0},packages:{"@storybook/react>util-deprecate":!0,"core-js-pure":!0,"crypto-browserify>browserify-sign>readable-stream>isarray":!0,"crypto-browserify>browserify-sign>readable-stream>safe-buffer":!0,"crypto-browserify>browserify-sign>readable-stream>string_decoder":!0,process:!0,"pumpify>inherits":!0,"readable-stream-2>core-util-is":!0,"readable-stream-2>process-nextick-args":!0,"webpack>events":!0}},"crypto-browserify>browserify-sign>readable-stream>safe-buffer":{packages:{buffer:!0}},"crypto-browserify>browserify-sign>readable-stream>string_decoder":{packages:{"crypto-browserify>browserify-sign>readable-stream>string_decoder>safe-buffer":!0}},"crypto-browserify>browserify-sign>readable-stream>string_decoder>safe-buffer":{packages:{buffer:!0}},"crypto-browserify>create-ecdh":{globals:{Buffer:!0},packages:{"@toruslabs/eccrypto>elliptic":!0,buffer:!0,"ethereumjs-util>bn.js":!0}},"crypto-browserify>create-hmac":{packages:{"@ngraveio/bc-ur>sha.js":!0,"ethereumjs-util>create-hash":!0,"ethereumjs-util>create-hash>cipher-base":!0,"ethereumjs-util>create-hash>ripemd160":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0}},"crypto-browserify>diffie-hellman":{globals:{Buffer:!0},packages:{buffer:!0,"crypto-browserify>diffie-hellman>miller-rabin":!0,"crypto-browserify>randombytes":!0,"ethereumjs-util>bn.js":!0}},"crypto-browserify>diffie-hellman>miller-rabin":{packages:{"@toruslabs/eccrypto>elliptic>brorand":!0,"ethereumjs-util>bn.js":!0}},"crypto-browserify>pbkdf2":{globals:{crypto:!0,process:!0,queueMicrotask:!0,setImmediate:!0,setTimeout:!0},packages:{"@ngraveio/bc-ur>sha.js":!0,"@ngraveio/bc-ur>sha.js>to-buffer":!0,"crypto-browserify>pbkdf2>create-hash":!0,"crypto-browserify>pbkdf2>ripemd160":!0,"mockttp>express>safe-buffer":!0,process:!0}},"crypto-browserify>pbkdf2>create-hash":{globals:{Buffer:!0},packages:{buffer:!0}},"crypto-browserify>pbkdf2>ripemd160":{globals:{Buffer:!0},packages:{buffer:!0,"crypto-browserify>pbkdf2>ripemd160>hash-base":!0,"pumpify>inherits":!0}},"crypto-browserify>pbkdf2>ripemd160>hash-base":{globals:{Buffer:!0},packages:{buffer:!0,"pumpify>inherits":!0,"stream-browserify":!0}},"crypto-browserify>public-encrypt":{packages:{"crypto-browserify>public-encrypt>browserify-rsa":!0,"crypto-browserify>public-encrypt>parse-asn1":!0,"crypto-browserify>randombytes":!0,"ethereumjs-util>bn.js":!0,"ethereumjs-util>create-hash":!0,"mockttp>express>safe-buffer":!0}},"crypto-browserify>public-encrypt>browserify-rsa":{packages:{"crypto-browserify>randombytes":!0,"ethereumjs-util>bn.js":!0,"mockttp>express>safe-buffer":!0}},"crypto-browserify>public-encrypt>parse-asn1":{packages:{"crypto-browserify>browserify-cipher>evp_bytestokey":!0,"crypto-browserify>pbkdf2":!0,"crypto-browserify>public-encrypt>parse-asn1>asn1.js":!0,"ethereumjs-util>ethereum-cryptography>browserify-aes":!0,"mockttp>express>safe-buffer":!0}},"crypto-browserify>public-encrypt>parse-asn1>asn1.js":{packages:{"@toruslabs/eccrypto>elliptic>minimalistic-assert":!0,buffer:!0,"ethereumjs-util>bn.js":!0,"pumpify>inherits":!0}},"crypto-browserify>randombytes":{globals:{crypto:!0,msCrypto:!0,"process.nextTick":!0},packages:{"mockttp>express>safe-buffer":!0,process:!0}},"crypto-browserify>randomfill":{globals:{crypto:!0,msCrypto:!0,"process.browser":!0,"process.nextTick":!0},packages:{"crypto-browserify>randombytes":!0,"mockttp>express>safe-buffer":!0,process:!0}},"currency-formatter":{packages:{"currency-formatter>accounting":!0,"currency-formatter>locale-currency":!0,"react>object-assign":!0}},"currency-formatter>accounting":{globals:{define:!0}},"currency-formatter>locale-currency":{globals:{countryCode:!0}},dompurify:{globals:{"console.warn":!0}},"eslint-plugin-react>array-includes>is-string":{packages:{"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bound":!0}},"eslint-plugin-react>es-iterator-helpers>has-property-descriptors":{packages:{"string.prototype.matchall>call-bind>es-define-property":!0}},"eslint-plugin-react>es-iterator-helpers>has-proto>dunder-proto":{packages:{"string.prototype.matchall>call-bind>call-bind-apply-helpers":!0,"string.prototype.matchall>gopd":!0}},"eslint-plugin-react>hasown":{packages:{"browserify>has>function-bind":!0}},"eth-ens-namehash":{globals:{Buffer:!0,name:"write"},packages:{buffer:!0,"eth-ens-namehash>idna-uts46-hx":!0,"eth-ens-namehash>js-sha3":!0}},"eth-ens-namehash>idna-uts46-hx":{globals:{define:!0},packages:{"eth-ens-namehash>idna-uts46-hx>punycode":!0}},"eth-ens-namehash>js-sha3":{globals:{define:!0,process:!0},packages:{process:!0}},"eth-lattice-keyring>@ethereumjs/util>micro-ftch":{globals:{"Buffer.concat":!0,Headers:!0,TextDecoder:!0,URL:!0,btoa:!0,fetch:!0,process:!0},packages:{"browserify>url":!0,"browserify>util":!0,buffer:!0,"https-browserify":!0,process:!0,"stream-http":!0}},"eth-lattice-keyring>gridplus-sdk>aes-js":{globals:{define:!0}},"eth-method-registry":{packages:{"eth-method-registry>@metamask/ethjs-contract":!0,"eth-method-registry>@metamask/ethjs-query":!0}},"eth-method-registry>@metamask/ethjs-contract":{packages:{"@babel/runtime":!0,"eth-ens-namehash>js-sha3":!0,"eth-method-registry>@metamask/ethjs-contract>@metamask/ethjs-filter":!0,"eth-method-registry>@metamask/ethjs-contract>@metamask/ethjs-util":!0,"eth-method-registry>@metamask/ethjs-contract>ethjs-abi":!0,"eth-method-registry>@metamask/ethjs-query>promise-to-callback":!0}},"eth-method-registry>@metamask/ethjs-contract>@metamask/ethjs-filter":{globals:{clearInterval:!0,setInterval:!0}},"eth-method-registry>@metamask/ethjs-contract>@metamask/ethjs-util":{globals:{"Buffer.byteLength":!0,"Buffer.from":!0},packages:{buffer:!0,"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>is-hex-prefixed":!0,"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>strip-hex-prefix":!0}},"eth-method-registry>@metamask/ethjs-contract>ethjs-abi":{globals:{Buffer:!0},packages:{buffer:!0,"eth-ens-namehash>js-sha3":!0,"eth-method-registry>@metamask/ethjs-contract>ethjs-abi>number-to-bn":!0,"ethereumjs-util>bn.js":!0}},"eth-method-registry>@metamask/ethjs-contract>ethjs-abi>number-to-bn":{packages:{"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>strip-hex-prefix":!0,"ethereumjs-util>bn.js":!0}},"eth-method-registry>@metamask/ethjs-query":{globals:{console:!0},packages:{"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format":!0,"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-rpc":!0,"eth-method-registry>@metamask/ethjs-query>promise-to-callback":!0}},"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format":{packages:{"@metamask/controller-utils>@metamask/ethjs-unit>@metamask/number-to-bn":!0,"eth-method-registry>@metamask/ethjs-contract>@metamask/ethjs-util":!0,"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>ethjs-schema":!0,"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>strip-hex-prefix":!0}},"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>strip-hex-prefix":{packages:{"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-format>is-hex-prefixed":!0}},"eth-method-registry>@metamask/ethjs-query>@metamask/ethjs-rpc":{packages:{"eth-method-registry>@metamask/ethjs-query>promise-to-callback":!0}},"eth-method-registry>@metamask/ethjs-query>promise-to-callback":{packages:{"eth-method-registry>@metamask/ethjs-query>promise-to-callback>is-fn":!0,"eth-method-registry>@metamask/ethjs-query>promise-to-callback>set-immediate-shim":!0}},"eth-method-registry>@metamask/ethjs-query>promise-to-callback>set-immediate-shim":{globals:{setImmediate:!0,"setTimeout.apply":!0},packages:{"core-js-pure":!0}},"ethereumjs-util":{globals:{Buffer:!0},packages:{"@ngraveio/bc-ur>assert":!0,buffer:!0,"ethereumjs-util>bn.js":!0,"ethereumjs-util>create-hash":!0,"ethereumjs-util>ethereum-cryptography":!0,"ethereumjs-util>rlp":!0}},"ethereumjs-util>bn.js":{globals:{Buffer:!0}},"ethereumjs-util>create-hash":{packages:{"@ngraveio/bc-ur>sha.js":!0,"ethereumjs-util>create-hash>cipher-base":!0,"ethereumjs-util>create-hash>md5.js":!0,"ethereumjs-util>create-hash>ripemd160":!0,"pumpify>inherits":!0}},"ethereumjs-util>create-hash>cipher-base":{packages:{"browserify>string_decoder":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0,"stream-browserify":!0}},"ethereumjs-util>create-hash>md5.js":{packages:{"ethereumjs-util>create-hash>md5.js>hash-base":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0}},"ethereumjs-util>create-hash>md5.js>hash-base":{packages:{"ethereumjs-util>create-hash>md5.js>hash-base>readable-stream":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0}},"ethereumjs-util>create-hash>md5.js>hash-base>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"ethereumjs-util>create-hash>ripemd160":{packages:{buffer:!0,"ethereumjs-util>create-hash>ripemd160>hash-base":!0,"pumpify>inherits":!0}},"ethereumjs-util>create-hash>ripemd160>hash-base":{packages:{"ethereumjs-util>create-hash>ripemd160>hash-base>readable-stream":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0}},"ethereumjs-util>create-hash>ripemd160>hash-base>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"ethereumjs-util>ethereum-cryptography":{globals:{"Buffer.from":!0},packages:{buffer:!0,"crypto-browserify>randombytes":!0,"ethereumjs-util>ethereum-cryptography>keccak":!0,"ethereumjs-util>ethereum-cryptography>secp256k1":!0}},"ethereumjs-util>ethereum-cryptography>browserify-aes":{globals:{"Buffer.concat":!0},packages:{buffer:!0,"crypto-browserify>browserify-cipher>evp_bytestokey":!0,"ethereumjs-util>create-hash>cipher-base":!0,"ethereumjs-util>ethereum-cryptography>browserify-aes>buffer-xor":!0,"mockttp>express>safe-buffer":!0,"pumpify>inherits":!0}},"ethereumjs-util>ethereum-cryptography>browserify-aes>buffer-xor":{globals:{Buffer:!0},packages:{buffer:!0}},"ethereumjs-util>ethereum-cryptography>bs58check":{packages:{"ethereumjs-util>create-hash":!0,"ethereumjs-util>ethereum-cryptography>bs58check>bs58":!0,"mockttp>express>safe-buffer":!0}},"ethereumjs-util>ethereum-cryptography>bs58check>bs58":{packages:{"@ensdomains/content-hash>multihashes>multibase>base-x":!0}},"ethereumjs-util>ethereum-cryptography>keccak":{globals:{"Buffer.alloc":!0,"Buffer.from":!0,"Buffer.isBuffer":!0},packages:{buffer:!0,"ethereumjs-util>ethereum-cryptography>keccak>readable-stream":!0}},"ethereumjs-util>ethereum-cryptography>keccak>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"ethereumjs-util>ethereum-cryptography>secp256k1":{packages:{"@toruslabs/eccrypto>elliptic":!0}},"ethereumjs-util>rlp":{globals:{"Buffer.concat":!0,"Buffer.from":!0,"Buffer.isBuffer":!0},packages:{buffer:!0,"ethereumjs-util>bn.js":!0}},ethers:{packages:{"@ethersproject/abi":!0,"@ethersproject/bytes":!0,"@ethersproject/hdnode":!0,"@ethersproject/transactions":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/base64":!0,"ethers>@ethersproject/basex":!0,"ethers>@ethersproject/hash":!0,"ethers>@ethersproject/json-wallets":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/random":!0,"ethers>@ethersproject/rlp":!0,"ethers>@ethersproject/sha2":!0,"ethers>@ethersproject/signing-key":!0,"ethers>@ethersproject/solidity":!0,"ethers>@ethersproject/strings":!0,"ethers>@ethersproject/units":!0,"ethers>@ethersproject/wallet":!0,"ethers>@ethersproject/web":!0}},"ethers>@ethersproject/abstract-provider":{packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0}},"ethers>@ethersproject/abstract-signer":{packages:{"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0}},"ethers>@ethersproject/address":{packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/rlp":!0}},"ethers>@ethersproject/base64":{globals:{atob:!0,btoa:!0},packages:{"@ethersproject/bytes":!0}},"ethers>@ethersproject/basex":{packages:{"@ethersproject/bytes":!0,"ethers>@ethersproject/properties":!0}},"ethers>@ethersproject/constants":{packages:{"@ethersproject/bignumber":!0}},"ethers>@ethersproject/hash":{packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/base64":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/strings":!0}},"ethers>@ethersproject/json-wallets":{packages:{"@ethersproject/bytes":!0,"@ethersproject/hdnode":!0,"@ethersproject/transactions":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/json-wallets>aes-js":!0,"ethers>@ethersproject/json-wallets>scrypt-js":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/pbkdf2":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/random":!0,"ethers>@ethersproject/strings":!0}},"ethers>@ethersproject/json-wallets>aes-js":{globals:{define:!0}},"ethers>@ethersproject/json-wallets>scrypt-js":{globals:{define:!0,setImmediate:!0,setTimeout:!0},packages:{"core-js-pure":!0}},"ethers>@ethersproject/keccak256":{packages:{"@ethersproject/bytes":!0,"eth-ens-namehash>js-sha3":!0}},"ethers>@ethersproject/logger":{globals:{console:!0}},"ethers>@ethersproject/networks":{packages:{"ethers>@ethersproject/logger":!0}},"ethers>@ethersproject/pbkdf2":{packages:{"@ethersproject/bytes":!0,"ethers>@ethersproject/sha2":!0}},"ethers>@ethersproject/properties":{packages:{"ethers>@ethersproject/logger":!0}},"ethers>@ethersproject/random":{globals:{"crypto.getRandomValues":!0},packages:{"@ethersproject/bytes":!0,"ethers>@ethersproject/logger":!0}},"ethers>@ethersproject/rlp":{packages:{"@ethersproject/bytes":!0,"ethers>@ethersproject/logger":!0}},"ethers>@ethersproject/sha2":{packages:{"@ethersproject/bytes":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/sha2>hash.js":!0}},"ethers>@ethersproject/sha2>hash.js":{packages:{"@toruslabs/eccrypto>elliptic>minimalistic-assert":!0,"pumpify>inherits":!0}},"ethers>@ethersproject/signing-key":{packages:{"@ethersproject/bytes":!0,"ethereumjs-util>bn.js":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/sha2>hash.js":!0}},"ethers>@ethersproject/solidity":{packages:{"@ethersproject/bignumber":!0,"@ethersproject/bytes":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/sha2":!0,"ethers>@ethersproject/strings":!0}},"ethers>@ethersproject/strings":{packages:{"@ethersproject/bytes":!0,"ethers>@ethersproject/constants":!0,"ethers>@ethersproject/logger":!0}},"ethers>@ethersproject/units":{packages:{"@ethersproject/bignumber":!0,"ethers>@ethersproject/logger":!0}},"ethers>@ethersproject/wallet":{packages:{"@ethersproject/bytes":!0,"@ethersproject/hdnode":!0,"@ethersproject/transactions":!0,"ethers>@ethersproject/abstract-provider":!0,"ethers>@ethersproject/abstract-signer":!0,"ethers>@ethersproject/address":!0,"ethers>@ethersproject/hash":!0,"ethers>@ethersproject/json-wallets":!0,"ethers>@ethersproject/keccak256":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/random":!0,"ethers>@ethersproject/signing-key":!0}},"ethers>@ethersproject/web":{globals:{clearTimeout:!0,fetch:!0,setTimeout:!0},packages:{"@ethersproject/bytes":!0,"ethers>@ethersproject/base64":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0,"ethers>@ethersproject/strings":!0}},"ethers>@ethersproject/wordlists":{packages:{"ethers>@ethersproject/hash":!0,"ethers>@ethersproject/logger":!0,"ethers>@ethersproject/properties":!0}},"extension-port-stream":{globals:{AggregateError:!0,"navigator.userAgent.includes":!0,"performance.now":!0,queueMicrotask:!0,scheduler:!0,setTimeout:!0},packages:{"readable-stream":!0}},"fuse.js":{globals:{console:!0,define:!0}},"gulp>vinyl-fs>object.assign":{packages:{"@lavamoat/webpack>json-stable-stringify>object-keys":!0,"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>define-properties":!0,"string.prototype.matchall>es-object-atoms":!0,"string.prototype.matchall>has-symbols":!0}},he:{globals:{define:!0}},"https-browserify":{packages:{"browserify>url":!0,"stream-http":!0}},"humanize-duration":{globals:{define:!0}},"jsdom>form-data>es-set-tostringtag>has-tostringtag":{packages:{"string.prototype.matchall>has-symbols":!0}},"lightweight-charts":{globals:{Image:!0,ResizeObserver:!0,URL:!0,cancelAnimationFrame:!0,chrome:!0,clearTimeout:!0,devicePixelRatio:!0,"document.activeElement":!0,"document.body":!0,"document.createElement":!0,"document.documentElement":!0,"document.getElementById":!0,"document.getSelection":!0,getComputedStyle:!0,"location.href":!0,"navigator.language":!0,"navigator.platform":!0,"navigator.userAgent.toLowerCase":!0,"navigator.userAgentData":!0,"performance.now":!0,queueMicrotask:!0,requestAnimationFrame:!0,setTimeout:!0},packages:{"lightweight-charts>fancy-canvas":!0}},"lightweight-charts>fancy-canvas":{globals:{ResizeObserver:!0,"document.body":!0}},localforage:{globals:{Blob:!0,BlobBuilder:!0,FileReader:!0,IDBKeyRange:!0,MSBlobBuilder:!0,MozBlobBuilder:!0,OIndexedDB:!0,WebKitBlobBuilder:!0,atob:!0,btoa:!0,"console.error":!0,"console.info":!0,"console.warn":!0,define:!0,fetch:!0,indexedDB:!0,localStorage:!0,mozIndexedDB:!0,msIndexedDB:!0,"navigator.platform":!0,"navigator.userAgent":!0,openDatabase:!0,setTimeout:!0,webkitIndexedDB:!0}},lodash:{globals:{_:!0,clearTimeout:!0,define:!0,setTimeout:!0}},loglevel:{globals:{console:!0,define:!0,"document.cookie":!0,localStorage:!0,log:"write",navigator:!0}},"lottie-web":{globals:{Blob:!0,Howl:!0,OffscreenCanvas:!0,"URL.createObjectURL":!0,Worker:!0,XMLHttpRequest:!0,bodymovin:"write",clearInterval:!0,console:!0,define:!0,"document.body":!0,"document.createElement":!0,"document.createElementNS":!0,"document.getElementsByClassName":!0,"document.getElementsByTagName":!0,"document.querySelectorAll":!0,"document.readyState":!0,"location.origin":!0,"location.pathname":!0,navigator:!0,requestAnimationFrame:!0,setInterval:!0,setTimeout:!0}},luxon:{globals:{Intl:!0}},"mockttp>@httptoolkit/subscriptions-transport-ws>symbol-observable":{globals:{module:!0}},"mockttp>express>qs":{packages:{"string.prototype.matchall>side-channel":!0}},"mockttp>express>safe-buffer":{packages:{buffer:!0}},nanoid:{globals:{"crypto.getRandomValues":!0}},"nock>debug":{globals:{console:!0,document:!0,localStorage:!0,navigator:!0,process:!0},packages:{"mocha>ms":!0,process:!0}},"openai>abort-controller":{globals:{AbortController:!0}},"path-browserify":{globals:{"process.cwd":!0},packages:{process:!0}},process:{globals:{clearTimeout:!0,setTimeout:!0}},"qrcode.react":{globals:{Path2D:!0,devicePixelRatio:!0},packages:{react:!0}},react:{packages:{"react>object-assign":!0}},"react-beautiful-dnd":{globals:{"Element.prototype":!0,__REDUX_DEVTOOLS_EXTENSION_COMPOSE__:!0,addEventListener:!0,cancelAnimationFrame:!0,clearTimeout:!0,console:!0,document:!0,getComputedStyle:!0,pageXOffset:!0,pageYOffset:!0,removeEventListener:!0,requestAnimationFrame:!0,scrollBy:!0,setTimeout:!0},packages:{"@babel/runtime":!0,react:!0,"react-beautiful-dnd>css-box-model":!0,"react-beautiful-dnd>memoize-one":!0,"react-beautiful-dnd>raf-schd":!0,"react-beautiful-dnd>use-memo-one":!0,"react-dom":!0,"react-redux":!0,redux:!0}},"react-beautiful-dnd>css-box-model":{globals:{getComputedStyle:!0,pageXOffset:!0,pageYOffset:!0},packages:{"react-beautiful-dnd>css-box-model>tiny-invariant":!0}},"react-beautiful-dnd>raf-schd":{globals:{cancelAnimationFrame:!0,requestAnimationFrame:!0}},"react-beautiful-dnd>use-memo-one":{packages:{react:!0}},"react-chartjs-2":{globals:{setTimeout:!0},packages:{"chart.js":!0,react:!0}},"react-compiler-runtime":{globals:{"console.error":!0},packages:{react:!0}},"react-devtools-core":{globals:{CSSStyleRule:!0,ElementTypeClass:!0,ElementTypeForwardRef:!0,ElementTypeFunction:!0,ElementTypeMemo:!0,ElementTypeVirtual:!0,ErrorEvent:!0,HTMLElement:!0,LOCAL_STORAGE_COMPONENT_FILTER_PREFERENCES_KEY:!0,LOCAL_STORAGE_OPEN_IN_EDITOR_URL:!0,"Node.ELEMENT_NODE":!0,SESSION_STORAGE_RECORD_CHANGE_DESCRIPTIONS_KEY:!0,SESSION_STORAGE_RECORD_TIMELINE_KEY:!0,SESSION_STORAGE_RELOAD_AND_PROFILE_KEY:!0,URL:!0,WebSocket:!0,__REACT_DEVTOOLS_COMPONENT_FILTERS__:!0,__REACT_DEVTOOLS_GLOBAL_HOOK__:!0,__REACT_DEVTOOLS_TARGET_WINDOW__:!0,cancelAnimationFrame:!0,chrome:!0,clearTimeout:!0,console:!0,define:!0,devicePixelRatio:!0,devtoolsJestTestScheduler:!0,dispatchEvent:!0,document:!0,getComputedStyle:!0,getInObject:!0,innerHeight:!0,innerWidth:!0,"localStorage.getItem":!0,"localStorage.removeItem":!0,"localStorage.setItem":!0,localStorageGetItem:!0,localStorageSetItem:!0,"navigator.userAgent":!0,performance:!0,queueMicrotask:!0,"regeneratorRuntime.mark":!0,"regeneratorRuntime.wrap":!0,reportError:!0,requestAnimationFrame:!0,"sessionStorage.getItem":!0,"sessionStorage.removeItem":!0,"sessionStorage.setItem":!0,sessionStorageGetItem:!0,sessionStorageRemoveItem:!0,sessionStorageSetItem:!0,setInObject:!0,setTimeout:!0}},"react-dom":{globals:{HTMLIFrameElement:!0,MSApp:!0,__REACT_DEVTOOLS_GLOBAL_HOOK__:!0,addEventListener:!0,clearTimeout:!0,clipboardData:!0,"console.error":!0,document:!0,event:!1,removeEventListener:!0,setTimeout:!0},packages:{react:!0,"react-dom>scheduler":!0,"react>object-assign":!0}},"react-dom>scheduler":{globals:{MessageChannel:!0,SharedArrayBuffer:!0,cancelAnimationFrame:!0,clearTimeout:!0,console:!0,performance:!0,requestAnimationFrame:!0,setTimeout:!0}},"react-focus-lock":{globals:{addEventListener:!0,"console.error":!0,"console.warn":!0,document:!0,removeEventListener:!0,setTimeout:!0},packages:{"@babel/runtime":!0,"prop-types":!0,react:!0,"react-focus-lock>focus-lock":!0,"react-focus-lock>react-clientside-effect":!0,"react-focus-lock>use-callback-ref":!0,"react-focus-lock>use-sidecar":!0}},"react-focus-lock>focus-lock":{globals:{HTMLIFrameElement:!0,"Node.DOCUMENT_FRAGMENT_NODE":!0,"Node.DOCUMENT_NODE":!0,"Node.DOCUMENT_POSITION_CONTAINED_BY":!0,"Node.DOCUMENT_POSITION_CONTAINS":!0,"Node.ELEMENT_NODE":!0,"console.error":!0,"console.warn":!0,document:!0,getComputedStyle:!0,setTimeout:!0}},"react-focus-lock>react-clientside-effect":{packages:{"@babel/runtime":!0,react:!0}},"react-focus-lock>use-callback-ref":{packages:{react:!0}},"react-focus-lock>use-sidecar":{packages:{tslib:!0}},"react-hot-toast":{globals:{MutationObserver:!0,clearTimeout:!0,matchMedia:!0,setTimeout:!0},packages:{react:!0,"react-hot-toast>goober":!0}},"react-hot-toast>goober":{globals:{__nonce__:!0,_goober:!0,"document.createElement":!0,"document.head":!0}},"react-idle-timer":{globals:{clearTimeout:!0,document:!0,setTimeout:!0},packages:{"prop-types":!0,react:!0}},"react-markdown":{globals:{"console.warn":!0},packages:{"prop-types":!0,react:!0,"react-markdown>comma-separated-tokens":!0,"react-markdown>property-information":!0,"react-markdown>react-is":!0,"react-markdown>remark-parse":!0,"react-markdown>remark-rehype":!0,"react-markdown>space-separated-tokens":!0,"react-markdown>style-to-object":!0,"react-markdown>unified":!0,"react-markdown>unist-util-visit":!0,"react-markdown>vfile":!0}},"react-markdown>property-information":{packages:{"watchify>xtend":!0}},"react-markdown>remark-parse":{packages:{"react-markdown>remark-parse>mdast-util-from-markdown":!0}},"react-markdown>remark-parse>mdast-util-from-markdown":{packages:{"react-markdown>remark-parse>mdast-util-from-markdown>mdast-util-to-string":!0,"react-markdown>remark-parse>mdast-util-from-markdown>micromark":!0,"react-markdown>vfile>unist-util-stringify-position":!0,"react-syntax-highlighter>refractor>parse-entities":!0}},"react-markdown>remark-parse>mdast-util-from-markdown>micromark":{packages:{"react-syntax-highlighter>refractor>parse-entities":!0}},"react-markdown>remark-rehype":{packages:{"react-markdown>remark-rehype>mdast-util-to-hast":!0}},"react-markdown>remark-rehype>mdast-util-to-hast":{globals:{"console.warn":!0},packages:{"@storybook/addon-docs>remark-external-links>mdast-util-definitions":!0,"react-markdown>remark-rehype>mdast-util-to-hast>mdurl":!0,"react-markdown>remark-rehype>mdast-util-to-hast>unist-builder":!0,"react-markdown>remark-rehype>mdast-util-to-hast>unist-util-generated":!0,"react-markdown>remark-rehype>mdast-util-to-hast>unist-util-position":!0,"react-markdown>unist-util-visit":!0}},"react-markdown>style-to-object":{packages:{"react-markdown>style-to-object>inline-style-parser":!0}},"react-markdown>unified":{packages:{"mocha>yargs-unparser>is-plain-obj":!0,"react-markdown>unified>bail":!0,"react-markdown>unified>extend":!0,"react-markdown>unified>is-buffer":!0,"react-markdown>unified>trough":!0,"react-markdown>vfile":!0}},"react-markdown>unist-util-visit":{packages:{"react-markdown>unist-util-visit>unist-util-visit-parents":!0}},"react-markdown>unist-util-visit>unist-util-visit-parents":{packages:{"react-markdown>unist-util-visit>unist-util-is":!0}},"react-markdown>vfile":{globals:{"process.cwd":!0},packages:{"path-browserify":!0,process:!0,"react-markdown>vfile>is-buffer":!0,"react-markdown>vfile>replace-ext":!0,"react-markdown>vfile>vfile-message":!0}},"react-markdown>vfile>replace-ext":{packages:{"path-browserify":!0}},"react-markdown>vfile>vfile-message":{packages:{"react-markdown>vfile>unist-util-stringify-position":!0}},"react-popper":{globals:{document:!0},packages:{"@popperjs/core":!0,react:!0,"react-popper>react-fast-compare":!0}},"react-popper>react-fast-compare":{globals:{Element:!0,"console.warn":!0}},"react-redux":{globals:{document:!0},packages:{"@babel/runtime":!0,"prop-types":!0,react:!0,"react-dom":!0,"react-redux>hoist-non-react-statics":!0,"react-redux>react-is":!0}},"react-redux>hoist-non-react-statics":{packages:{"react-redux>hoist-non-react-statics>react-is":!0}},"react-router-dom":{globals:{FormData:!0,URL:!0,URLSearchParams:!0,__reactRouterVersion:"write",addEventListener:!0,confirm:!0,document:!0,history:!0,"location.href":!0,removeEventListener:!0,scrollTo:!0,scrollY:!0,"sessionStorage.getItem":!0,"sessionStorage.setItem":!0,setTimeout:!0},packages:{react:!0,"react-dom":!0,"react-router-dom>@remix-run/router":!0,"react-router-dom>react-router":!0}},"react-router-dom>@remix-run/router":{globals:{AbortController:!0,DOMException:!0,FormData:!0,Headers:!0,Request:!0,Response:!0,URL:!0,URLSearchParams:!0,console:!0,"document.defaultView":!0,history:!0}},"react-router-dom>react-router":{globals:{"console.error":!0,"console.warn":!0},packages:{react:!0,"react-router-dom>@remix-run/router":!0}},"react-simple-file-input":{globals:{File:!0,FileReader:!0,"console.warn":!0},packages:{"prop-types":!0,react:!0}},"react-syntax-highlighter>refractor>parse-entities":{globals:{"document.createElement":!0}},"react-tippy":{globals:{Element:!0,MSStream:!0,MutationObserver:!0,addEventListener:!0,clearTimeout:!0,"console.error":!0,"console.warn":!0,define:!0,document:!0,getComputedStyle:!0,innerHeight:!0,innerWidth:!0,"navigator.maxTouchPoints":!0,"navigator.msMaxTouchPoints":!0,"navigator.userAgent":!0,performance:!0,requestAnimationFrame:!0,setTimeout:!0},packages:{react:!0,"react-dom":!0,"react-tippy>popper.js":!0}},"react-tippy>popper.js":{globals:{MSInputMethodContext:!0,"Node.DOCUMENT_POSITION_FOLLOWING":!0,cancelAnimationFrame:!0,"console.warn":!0,devicePixelRatio:!0,document:!0,getComputedStyle:!0,innerHeight:!0,innerWidth:!0,"navigator.userAgent":!0,requestAnimationFrame:!0,setTimeout:!0}},"react-toggle-button":{globals:{cancelAnimationFrame:!0,clearTimeout:!0,"console.warn":!0,define:!0,performance:!0,requestAnimationFrame:!0,setTimeout:!0},packages:{react:!0}},"react-transition-group":{globals:{Element:!0,setTimeout:!0},packages:{"@babel/runtime":!0,"prop-types":!0,react:!0,"react-dom":!0,"react-transition-group>dom-helpers":!0}},"readable-stream":{globals:{AbortController:!0,AbortSignal:!0,AggregateError:!0,Blob:!0,queueMicrotask:!0},packages:{"browserify>string_decoder":!0,buffer:!0,"openai>abort-controller":!0,process:!0,"webpack>events":!0}},"readable-stream-2>core-util-is":{globals:{"Buffer.isBuffer":!0},packages:{buffer:!0}},"readable-stream-2>process-nextick-args":{globals:{process:!0},packages:{process:!0}},redux:{globals:{console:!0},packages:{"@babel/runtime":!0}},"remote-redux-devtools":{globals:{"console.log":!0,"console.warn":!0,fetch:!0,setTimeout:!0},packages:{"remote-redux-devtools>jsan":!0,"remote-redux-devtools>redux-devtools-core":!0,"remote-redux-devtools>redux-devtools-instrument":!0,"remote-redux-devtools>rn-host-detect":!0,"remote-redux-devtools>socketcluster-client":!0}},"remote-redux-devtools>jsan":{globals:{"console.warn":!0}},"remote-redux-devtools>redux-devtools-core":{globals:{ErrorUtils:!0,console:!0,devToolsOptions:!0,onerror:"write",serializeState:!0},packages:{lodash:!0,"remote-redux-devtools>jsan":!0,"remote-redux-devtools>redux-devtools-core>get-params":!0,"remote-redux-devtools>redux-devtools-core>nanoid":!0,"remote-redux-devtools>redux-devtools-core>remotedev-serialize":!0}},"remote-redux-devtools>redux-devtools-core>get-params":{globals:{GetParams:"write"}},"remote-redux-devtools>redux-devtools-instrument":{globals:{chrome:!0,"console.error":!0,process:!0,setTimeout:!0},packages:{lodash:!0,"mockttp>@httptoolkit/subscriptions-transport-ws>symbol-observable":!0,process:!0}},"remote-redux-devtools>rn-host-detect":{globals:{__DEV__:!0,__fbBatchedBridgeConfig:!0,console:!0}},"remote-redux-devtools>socketcluster-client":{globals:{WebSocket:!0,WorkerGlobalScope:!0,addEventListener:!0,clearTimeout:!0,localStorage:!0,location:!0,removeEventListener:!0,setTimeout:!0},packages:{"remote-redux-devtools>socketcluster-client>buffer":!0,"remote-redux-devtools>socketcluster-client>clone":!0,"remote-redux-devtools>socketcluster-client>component-emitter":!0,"remote-redux-devtools>socketcluster-client>linked-list":!0,"remote-redux-devtools>socketcluster-client>querystring":!0,"remote-redux-devtools>socketcluster-client>sc-channel":!0,"remote-redux-devtools>socketcluster-client>sc-errors":!0,"remote-redux-devtools>socketcluster-client>sc-formatter":!0,"remote-redux-devtools>socketcluster-client>uuid":!0}},"remote-redux-devtools>socketcluster-client>buffer":{globals:{console:!0},packages:{"base64-js":!0,"buffer>ieee754":!0}},"remote-redux-devtools>socketcluster-client>clone":{globals:{Buffer:!0},packages:{"remote-redux-devtools>socketcluster-client>buffer":!0}},"remote-redux-devtools>socketcluster-client>sc-channel":{packages:{"remote-redux-devtools>socketcluster-client>component-emitter":!0}},"remote-redux-devtools>socketcluster-client>sc-formatter":{globals:{Buffer:!0}},"remote-redux-devtools>socketcluster-client>uuid":{globals:{crypto:!0,msCrypto:!0}},reselect:{globals:{WeakRef:!0,"console.warn":!0}},semver:{globals:{"console.error":!0,process:!0},packages:{process:!0}},"stream-browserify":{packages:{"pumpify>inherits":!0,"stream-browserify>readable-stream":!0,"webpack>events":!0}},"stream-browserify>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"stream-http":{globals:{AbortController:!0,Blob:!0,"Buffer.alloc":!0,"Buffer.from":!0,MSStreamReader:!0,ReadableStream:!0,WritableStream:!0,XDomainRequest:!0,XMLHttpRequest:!0,clearTimeout:!0,fetch:!0,"location.protocol.search":!0,"process.nextTick":!0,setTimeout:!0},packages:{"browserify>url":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"stream-http>builtin-status-codes":!0,"stream-http>readable-stream":!0,"watchify>xtend":!0}},"stream-http>readable-stream":{globals:{"process.nextTick":!0,"process.stderr":!0,"process.stdout":!0},packages:{"@storybook/react>util-deprecate":!0,"browserify>string_decoder":!0,buffer:!0,process:!0,"pumpify>inherits":!0,"webpack>events":!0}},"string.prototype.matchall>call-bind":{packages:{"string.prototype.matchall>call-bind>call-bind-apply-helpers":!0,"string.prototype.matchall>call-bind>es-define-property":!0,"string.prototype.matchall>call-bind>set-function-length":!0,"string.prototype.matchall>get-intrinsic":!0}},"string.prototype.matchall>call-bind>call-bind-apply-helpers":{packages:{"browserify>has>function-bind":!0,"string.prototype.matchall>es-errors":!0}},"string.prototype.matchall>call-bind>set-function-length":{packages:{"eslint-plugin-react>es-iterator-helpers>has-property-descriptors":!0,"string.prototype.matchall>define-properties>define-data-property":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>get-intrinsic":!0,"string.prototype.matchall>gopd":!0}},"string.prototype.matchall>call-bound":{packages:{"string.prototype.matchall>call-bind>call-bind-apply-helpers":!0,"string.prototype.matchall>get-intrinsic":!0}},"string.prototype.matchall>define-properties":{packages:{"@lavamoat/webpack>json-stable-stringify>object-keys":!0,"eslint-plugin-react>es-iterator-helpers>has-property-descriptors":!0,"string.prototype.matchall>define-properties>define-data-property":!0}},"string.prototype.matchall>define-properties>define-data-property":{packages:{"string.prototype.matchall>call-bind>es-define-property":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>gopd":!0}},"string.prototype.matchall>es-abstract>array-buffer-byte-length":{packages:{"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-abstract>is-array-buffer":!0}},"string.prototype.matchall>es-abstract>available-typed-arrays":{packages:{"string.prototype.matchall>es-abstract>typed-array-length>possible-typed-array-names":!0}},"string.prototype.matchall>es-abstract>es-to-primitive>is-symbol":{packages:{"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-abstract>safe-regex-test":!0,"string.prototype.matchall>has-symbols":!0}},"string.prototype.matchall>es-abstract>get-proto":{packages:{"eslint-plugin-react>es-iterator-helpers>has-proto>dunder-proto":!0,"string.prototype.matchall>es-object-atoms":!0}},"string.prototype.matchall>es-abstract>is-array-buffer":{packages:{"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>get-intrinsic":!0}},"string.prototype.matchall>es-abstract>is-callable":{globals:{document:!0}},"string.prototype.matchall>es-abstract>is-regex":{packages:{"eslint-plugin-react>hasown":!0,"jsdom>form-data>es-set-tostringtag>has-tostringtag":!0,"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>gopd":!0}},"string.prototype.matchall>es-abstract>is-shared-array-buffer":{packages:{"string.prototype.matchall>call-bound":!0}},"string.prototype.matchall>es-abstract>object-inspect":{globals:{HTMLElement:!0,WeakRef:!0}},"string.prototype.matchall>es-abstract>safe-regex-test":{packages:{"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-abstract>is-regex":!0,"string.prototype.matchall>es-errors":!0}},"string.prototype.matchall>es-abstract>stop-iteration-iterator":{globals:{StopIteration:!0},packages:{"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>internal-slot":!0}},"string.prototype.matchall>es-abstract>typed-array-buffer":{packages:{"browserify>util>is-typed-array":!0,"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-errors":!0}},"string.prototype.matchall>get-intrinsic":{globals:{AggregateError:!0,Atomics:!0,FinalizationRegistry:!0,Float16Array:!0,SharedArrayBuffer:!0,WeakRef:!0},packages:{"browserify>has>function-bind":!0,"eslint-plugin-react>array-includes>math-intrinsics":!0,"eslint-plugin-react>hasown":!0,"string.prototype.matchall>call-bind>call-bind-apply-helpers":!0,"string.prototype.matchall>call-bind>es-define-property":!0,"string.prototype.matchall>es-abstract>get-proto":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>es-object-atoms":!0,"string.prototype.matchall>get-intrinsic>async-function":!0,"string.prototype.matchall>get-intrinsic>async-generator-function":!0,"string.prototype.matchall>get-intrinsic>generator-function":!0,"string.prototype.matchall>gopd":!0,"string.prototype.matchall>has-symbols":!0}},"string.prototype.matchall>internal-slot":{packages:{"eslint-plugin-react>hasown":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>side-channel":!0}},"string.prototype.matchall>regexp.prototype.flags":{packages:{"string.prototype.matchall>call-bind":!0,"string.prototype.matchall>define-properties":!0,"string.prototype.matchall>es-abstract>get-proto":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>gopd":!0,"string.prototype.matchall>set-function-name":!0}},"string.prototype.matchall>set-function-name":{packages:{"eslint-plugin-react>es-iterator-helpers>has-property-descriptors":!0,"string.prototype.matchall>define-properties>define-data-property":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>set-function-name>functions-have-names":!0}},"string.prototype.matchall>side-channel":{packages:{"string.prototype.matchall>es-abstract>object-inspect":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>side-channel>side-channel-list":!0,"string.prototype.matchall>side-channel>side-channel-map":!0,"string.prototype.matchall>side-channel>side-channel-weakmap":!0}},"string.prototype.matchall>side-channel>side-channel-list":{packages:{"string.prototype.matchall>es-abstract>object-inspect":!0,"string.prototype.matchall>es-errors":!0}},"string.prototype.matchall>side-channel>side-channel-map":{packages:{"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-abstract>object-inspect":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>get-intrinsic":!0}},"string.prototype.matchall>side-channel>side-channel-weakmap":{packages:{"string.prototype.matchall>call-bound":!0,"string.prototype.matchall>es-abstract>object-inspect":!0,"string.prototype.matchall>es-errors":!0,"string.prototype.matchall>get-intrinsic":!0,"string.prototype.matchall>side-channel>side-channel-map":!0}},tslib:{globals:{SuppressedError:!0}},tweetnacl:{globals:{crypto:!0,msCrypto:!0,nacl:"write"}},"uri-js":{globals:{define:!0}},uuid:{globals:{crypto:!0,msCrypto:!0}},"wait-on>axios":{globals:{AbortController:!0,Blob:!0,Buffer:!0,FormData:!0,ReadableStream:!0,Request:!0,Response:!0,TextEncoder:!0,URL:!0,URLSearchParams:!0,WorkerGlobalScope:!0,XMLHttpRequest:!0,btoa:!0,clearTimeout:!0,"console.warn":!0,document:!0,fetch:!0,importScripts:!0,"location.href":!0,navigator:!0,postMessage:!0,process:!0,queueMicrotask:!0,setImmediate:!0,setTimeout:!0},packages:{buffer:!0,"core-js-pure":!0,process:!0}},"wait-on>rxjs":{globals:{clearTimeout:!0,"setTimeout.apply":!0},packages:{tslib:!0}},"web-vitals":{globals:{"PerformanceEventTiming.prototype":!0,PerformanceObserver:!0,addEventListener:!0,"document.addEventListener":!0,"document.prerendering":!0,"document.readyState":!0,"document.visibilityState":!0,"document.wasDiscarded":!0,performance:!0,removeEventListener:!0,requestAnimationFrame:!0,requestIdleCallback:!0,setTimeout:!0}},"webextension-polyfill":{globals:{browser:!0,chrome:!0,"console.error":!0,"console.warn":!0,define:!0}},"webpack>events":{globals:{console:!0}}}},e.ENUM={NAME_globalThis:"G",NAME_scopeTerminator:"ST",NAME_runtimeHandler:"RH",RUNTIME_KEY:"_LM_"},(()=>{let t={exports:{}};function r(e,t){return e&&0!==e.length?`${e}.${t}`:t}function a(e,t,a){let s=Reflect.getOwnPropertyDescriptor(t,e[0])?.enumerable,o=a,n="";for(let t=0;t<e.length-1;t++){n=r(n,e[t]);let a=e[t];if(Reflect.getOwnPropertyDescriptor(o,a)?.get)throw Error(`LavaMoat - "${e[0]}" is writeable elsewhere and both "${n}" and "${e.join(".")}" are allowed for one package. One of these entries is redundant.`);"object"!=typeof o[a]&&(o[a]={}),o=o[a]}Reflect.defineProperty(o,e[e.length-1],{get:()=>{let r=t[e[0]],a=t;for(let t=1;t<e.length;t++)a=r,r=r[e[t]];return"function"==typeof r&&(r=r.bind(a)),r},writeable:!1,enumerable:s,configurable:!1})}function s(e,t,r){let a=function(){return new.target?Reflect.construct(e,arguments,new.target):Reflect.apply(e,t(this)?r:this,arguments)};return Object.defineProperties(a,Object.getOwnPropertyDescriptors(e)),Reflect.getPrototypeOf(a)!==Reflect.getPrototypeOf(e)&&Object.setPrototypeOf(a,Reflect.getPrototypeOf(e)),a}t.exports,t.exports=function({createFunctionWrapper:e=s,handleGlobalWrite:t=!1,knownWritableFields:o=new Set}={}){return{getEndowmentsForConfig:function(e,r,a,s){if(!r.globals)return{};let o=[],c=new Set,l=[];return Object.entries(r.globals).forEach(([e,r])=>{let a=e.split(".");if(a.some(e=>"__proto__"===e))throw Error(`Lavamoat - "__proto__" disallowed when creating minimal view. saw "${e}"`);if(!1===r)return void l.push(e);if("write"===r){if(!t)return;if(a.length>1)throw Error(`LavaMoat - write access is only allowed at the top level, saw "${e}"`);c.add(e),o.push(e);return}if(!0!==r)throw Error(`LavaMoat - unrecognizable policy value (${typeof r}) for path "${e}"`);o.push(e)}),o.sort((e,t)=>e.length-t.length),n(e,o,a,s,l,c)},copyWrappedGlobals:function(e,t,r=["globalThis"]){let a=function(e){let t=[],r=e;for(;r&&("object"==typeof r||"function"==typeof r);)t.push(r),r=Reflect.getPrototypeOf(r);return t}(e),s=a.findIndex(e=>e===Object.prototype),o=-1===s;o&&(s=a.length);let n=a.slice(0,s);n.forEach(t=>{Object.values(Object.getOwnPropertyDescriptors(t)).forEach(t=>{if("get"in t&&t.get)try{Reflect.apply(t.get,e,[])}catch{}})});let c=n.map((e,t)=>{let r=Object.getOwnPropertyDescriptors(e);return o&&t===n.length-1?Object.fromEntries(Object.entries(r).filter(([e])=>!(e in Object.prototype))):r});for(let a of(Object.entries(Object.assign(Object.create(null),...c.reverse())).filter(([e])=>!(e in t)).filter(([e])=>!r.includes(e)).forEach(([r,a])=>{let s=i(a,t,e);Reflect.defineProperty(t,r,s)}),r))a in t||(t[a]=t);return t},getBuiltinForConfig:function(e,t,r){let a=[],s=[];return Object.entries(r).forEach(([e,r])=>{let o=e.split(".");if(t===o[0]){let e=o.slice(1).join(".");!0===r?a.push(e):!1===r&&s.push(e)}}),c(e,a,s)},createFunctionWrapper:e,attenuateBuiltin:c,makeMinimalViewOfRef:n,copyValueAtPath:l,applyGetSetPropDescTransforms:m,applyEndowmentPropDescTransforms:i};function n(e,t,r,s,c=[],i=new Set){let m={};return t.forEach(t=>{let n=t.split(".");o.has(n[0])?i.has(n[0])?function(e,t,r){let a=Reflect.getOwnPropertyDescriptor(t,e)?.enumerable;Reflect.defineProperty(r,e,{configurable:!1,enumerable:a,set(r){t[e]=r},get:()=>t[e]})}(n[0],e,m):a(n,e,m):l("",n,c,e,m,r,s)}),m}function c(e,t,r=[]){return n(e,t.sort(),void 0,void 0,r)}function l(t,a,s,o,n,c=o,i=n){if(0===a.length)throw Error("unable to copy, must have pathParts, was empty");let[p,...u]=a,h=r(t,p),{prop:g}=function(e,t){let r=e;for(;;){if(!r)return{prop:null,receiver:null};let e=typeof r;if("object"===e||"function"===e){let e=Reflect.getOwnPropertyDescriptor(r,t);if(e)return{receiver:r,prop:e};r=Reflect.getPrototypeOf(r)}else r=r.__proto__}}(o,p);if(!g)return;let d=Reflect.getOwnPropertyDescriptor(n,p);if(d){if(!("value"in d))throw Error(`unable to copy on to targetRef, targetRef has a getter at "${h}"`);let e=typeof d.value;if("object"!==e&&"function"!==e)throw Error(`unable to copy on to targetRef, targetRef value is not an obj or func at "${h}"`)}if(u.length>0){let e,{sourceValue:t,sourceWritable:r}=y(g);if(d&&!s.includes(h))e=d.value;else{let t={};Reflect.defineProperty(n,p,{value:t,writable:r,enumerable:g.enumerable,configurable:g.configurable}),e=t}l(h,u,s,t,e);return}if(s.includes(h))return void console.warn(`LavaMoat - conflicting rules exist for "${h}"`);if(!("value"in g))return void Reflect.defineProperty(n,p,m(g,i,c));let{sourceValue:b,sourceWritable:k}=y(g);if("function"!=typeof b)return void Reflect.defineProperty(n,p,g);function y(e){let t,r;if("value"in e)t=e.value,r=e.writable;else if("get"in e&&e.get)t=e.get.call(c),r="set"in e;else throw Error("getEndowmentsForConfig - property descriptor missing a getter");return{sourceValue:t,sourceWritable:r}}Reflect.defineProperty(n,p,{value:e(b,e=>e===i,c),writable:k,enumerable:g.enumerable,configurable:g.configurable})}function i(t,r,a){let s=t;return m(s=function(t,r,a){if(!("value"in t&&"function"==typeof t.value))return t;let s=e(t.value,e=>e===r,a);return{...t,value:s}}(s,r,a),r,a)}function m(t,r,a){let s={...t};return t.get&&(s.get=function(){let s=Reflect.apply(t.get,this===r?a:this,[]);return"function"==typeof s?e(s,e=>e===r,a):s}),t.set&&(s.set=function(e){let s=this===r?a:this;return Reflect.apply(t.set,s,[e])}),s}},t.exports.defaultCreateFunctionWrapper=s,t.exports._test={instrumentDynamicValueAtPath:a},e.endowmentsToolkit=t.exports})(),(()=>{let t={exports:{}},r=t.exports;"event"in globalThis&&(globalThis.event=void 0);let{getOwnPropertyNames:a}=Object;function s(e){let t=[],r=e;for(;r&&("object"==typeof r||"function"==typeof r);)t.push(r),r=Reflect.getPrototypeOf(r);return t}!function(e){if("window"in e&&"object"==typeof e.window&&e!==e.window){let t=e.window,r=s(t),o=s(e);r.pop();let n=r.flatMap(e=>a(e)),c=new Set(o.flatMap(e=>a(e)));for(let r of n)if(!c.has(r)&&r in globalThis&&void 0!==t[r])try{e[r]=e[r]}catch{}}}(globalThis);let{defineProperty:o}=Object,{call:n}=Function.prototype,c=new WeakMap,l=globalThis,i=MessageEvent.prototype,m=new Compartment().globalThis,p=Object.getOwnPropertyDescriptor(i,"source");if(p&&p.get){let e=n.bind(p.get);o(i,"source",{...p,get(){let t=e(this);return t===l||t===l.window?c.get(this)||m:t}})}r.MessageEvent=(e,t,r)=>{let a=e.MessageEvent;a&&(e.MessageEvent=function(e,t){let s=new a(e,t);return c.set(s,r),s},e.MessageEvent.prototype=a.prototype)},r.addEventListener=(e,t,r)=>{let a=e.addEventListener;a&&(e.addEventListener=(e,s,o)=>"message"===e?a.call(t,e,e=>(c.set(e,r),s.call(r,e)),o):a.call(r,e,s,o))},e.repairs=t.exports})(),(()=>{let t,r={exports:{}};r.exports;let{repairIntrinsics:a}=globalThis,s="object"==typeof console?console.warn:()=>{},o=void 0!==a;o?(a(e.options.lockdown),c.forEach(e=>{e()}),hardenIntrinsics()):s("LavaMoatPlugin: runtime execution started without SES present, switching to no-op.");let{keys:n,create:l,freeze:i,assign:m,defineProperty:p,defineProperties:u,getOwnPropertyDescriptors:h,fromEntries:g,entries:d,values:b}=Object,{Proxy:k,Math:y,Date:f}=globalThis,{harden:j}=globalThis,w=new Set;b(e.policy.resources).forEach(e=>{e.globals&&"object"==typeof e.globals&&d(e.globals).forEach(([e,t])=>{"write"===t&&w.add(e)})});let{getEndowmentsForConfig:v,copyWrappedGlobals:x,getBuiltinForConfig:E}=e.endowmentsToolkit({handleGlobalWrite:!0,knownWritableFields:w}),{NAME_globalThis:T,NAME_scopeTerminator:O,NAME_runtimeHandler:_}=e.ENUM,q=i(new k(i(l(null)),i({has:i(()=>!0)}))),R=globalThis,L=["window","self","global","globalThis","frames"],S=n(e.repairs||{}),D=new Map,M=t=>{let r=e.idmap.find(([,e])=>e.includes(t));if(r)return r[0]};e.defaultExport=i((r,a)=>{if(!o)return l(null);if(!D.has(r)){let a=new Compartment({Math:y,Date:f});((r,a)=>{if(r===e.root)x(R,t=a,L),e?.scuttling?.scuttle(R,e.options?.scuttleGlobalThis);else{let s=e.policy.resources[r]||{},o=v(t,s,globalThis,a);S.length>0&&s.globals&&n(s.globals).length>0&&S.forEach(t=>{if(o[t]){let r=e.repairs[t];r&&r(o,R,a)}}),u(a,{...h(o),...g(L.map(e=>[e,{value:a}]))}),e.debug&&e.debug.debugProxy(a,t,r)}})(r,a.globalThis),D.set(r,a)}let c=l(null),{__webpack_require__:d}=a,{module:b}=a;if(d){let t=function(t,...a){"number"!=typeof t&&(t=`${t}`);let s=d.bind(this,t,...a);var o=t;if(void 0===o)throw Error("Requested specifier is undefined");if(e.unenforceable.includes(o)||r===e.root)return s();let c=e.policy.resources[r]||{};if(e.externals[o]){let t=e.externals[o];if(c.builtin){if(c.builtin[t])return s();if(t&&!t.includes(".")&&n(c.builtin).some(e=>e.startsWith(`${t}.`)))return E(s(),t,c.builtin)}if(c.packages){let e=M(t);if(e&&c.packages[e])return s()}}let l=M(o);if(!l){if(e.ctxm.includes(o))throw Error(`'${r}' is trying to load a module dynamically from a dependency it has not been allowed using the following Webpack Context Module: '${o}'`);throw Error(`Requested specifier '${o}' is not allowed as a builtin and is not a known dependency of '${r}'; regenerate policy or add it to policy-override.json.`)}if(l===r||c.packages?.[l])return s();throw Error(`Policy does not allow importing ${l} from ${r}`)};for(let a of(t.e=t=>{if(!e.kch.includes(t))throw Error(`Attempt to load a chunk that was not known at compile time: ${t} from ${r}`);return d.e(t)},["O","n","d","o","r","s","t","b","j"]))t[a]=j(d[a]);t.m=new k({},{has:(e,t)=>(s(`A module attempted to read ${String(t)} directly from webpack's module cache`),!1)}),t.g=D.get(r).globalThis,t.nmd=e=>e===b?d.nmd(b):e,t.hmd=e=>e===b?d.hmd(b):e,c.__webpack_require__=t}let w=m(l(null),a,c);p(w,"module",{get:()=>b,set:()=>{}});let z=w.exports;return p(w,"exports",{get:()=>z,set:e=>{z=e}}),i(w),i(m(l(null),{[O]:q,[_]:w,[T]:D.get(r).globalThis}))}),e.runtime=r.exports})(),r._LM_=e.defaultExport,"undefined"!=typeof harden&&harden(r._LM_)})()})();